const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const workflow = fs.readFileSync('.github/workflows/monthly-fetch.yml', 'utf8');
const script = workflow.split('          script: |\n')[1].split('\n').map(line => line.slice(12)).join('\n');
const execute = new (Object.getPrototypeOf(async function() {}).constructor)('github', 'context', 'core', 'process', script);
function issue(number, run, status='failure', extra={}) {
  return {number, title:`📅 Monthly RealityCheck Run – ${status}`, state:'open',
    user:{login:'github-actions[bot]'}, assignees:[], milestone:null,
    body:`<!-- realitycheck-monthly-status:${run} -->\n<!-- realitycheck-monthly-attempt:${run}:1 -->\n- **Branch**: main\n`, ...extra};
}
async function run({status='success', issues=[], comments={}, ref='refs/heads/main', id=200, attempt='1'}={}) {
  const calls=[];
  const api={};
  for (const method of ['listForRepo','listComments','create','update','createComment']) {
    api[method]=async args=>{calls.push({method,...args});return {data:method==='create'?{number:500}:args};};
  }
  const github={rest:{issues:api}, paginate:async(method,args)=> method===api.listForRepo?issues:(comments[args.issue_number]||[])};
  await execute(github, {repo:{owner:'ckvfox',repo:'realitycheck'}, ref,runId:id}, {notice:()=>{}}, {env:{RUN_STATUS:status, DEFAULT_BRANCH:'main',GITHUB_RUN_ATTEMPT:attempt,GITHUB_SERVER_URL:'https://github.com'}});
  return calls;
}
test('success archives its record and resolves only older managed notifications',async()=>{
  const calls=await run({issues:[issue(1,100)]});
  assert.equal(calls.filter(c=>c.method==='create').length,1);
  assert.ok(calls.some(c=>c.method==='update'&&c.issue_number===500&&c.state==='closed'));
  assert.ok(calls.some(c=>c.method==='createComment'&&c.issue_number===1&&c.body.includes('actions/runs/200')));
  assert.ok(calls.some(c=>c.method==='update'&&c.issue_number===1&&c.state==='closed'));
});
test('failure and cancellation remain open without resolving prior errors',async()=>{
  for (const status of ['failure','cancelled']) {
    const calls=await run({status,issues:[issue(1,100)]});
    assert.equal(calls.filter(c=>c.method==='create').length,1);
    assert.equal(calls.filter(c=>c.method==='update').length,0);
  }
});
test('human tasks, discussion, other workflows and newer failures are protected',async()=>{
  const issues=[issue(1,100,'failure',{assignees:[{login:'ckvfox'}]}),
    issue(2,100,'failure',{milestone:{number:1}}),issue(3,100),
    issue(4,300),issue(5,100,'failure',{user:{login:'ckvfox'}}),
    issue(6,100,'failure',{body:'a real task'}),
    issue(7,100,'failure',{pull_request:{}}),
    issue(8,100,'failure',{body:issue(8,100).body.replace('main','feature')})];
  const calls=await run({issues,comments:{3:[{user:{login:'ckvfox'},body:'Investigate further'}]}});
  assert.equal(calls.filter(c=>c.method==='update'&&c.issue_number!==500).length,0);
});
test('same run and attempt is idempotent',async()=>{
  const calls=await run({issues:[issue(1,200)]});
  assert.equal(calls.filter(c=>c.method==='create').length,0);
  assert.equal(calls.filter(c=>c.method==='createComment').length,0);
  assert.equal(calls.filter(c=>c.method==='update').length,1);
});
test('rerun preserves the old attempt and reopens a failure',async()=>{
  const calls=await run({status:'failure',attempt:'2',issues:[issue(1,200,'success',{state:'closed'})]});
  assert.ok(calls.some(c=>c.method==='createComment'&&c.body.includes('monthly-attempt:200:1')));
  assert.ok(calls.some(c=>c.method==='update'&&c.state==='open'&&c.body.includes('monthly-attempt:200:2')));
});
test('retry after partial API failure does not duplicate attempt or recovery comments',async()=>{
  const calls=await run({attempt:'2',issues:[issue(1,200),issue(2,100)],comments:{
    1:[{body:'<!-- realitycheck-monthly-attempt:200:1 -->',user:{login:'github-actions[bot]'}}],
    2:[{body:'<!-- realitycheck-monthly-recovery:200 -->',user:{login:'github-actions[bot]'}}]
  }});
  assert.equal(calls.filter(c=>c.method==='createComment').length,0);
});
test('feature-branch dispatch cannot alter production notifications',async()=>{
  assert.deepEqual(await run({ref:'refs/heads/feature',issues:[issue(1,100)]}),[]);
});
test('unexpected status fails visibly',async()=>{
  await assert.rejects(run({status:'unknown'}),/Unexpected run status/);
});

test('rerun never closes a status record adopted as a human task',async()=>{
  const calls=await run({issues:[issue(1,200)],comments:{1:[{user:{login:'ckvfox'},body:'Track follow-up'}]}});
  assert.equal(calls.filter(c=>c.method==='update').length,0);
  assert.equal(calls.filter(c=>c.method==='createComment').length,1);
});
