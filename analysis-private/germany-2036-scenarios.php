<?php
declare(strict_types=1);

if (isset($_SERVER['SCRIPT_FILENAME']) && realpath((string) $_SERVER['SCRIPT_FILENAME']) === __FILE__) {
    header('X-Robots-Tag: noindex, nofollow, noarchive', true);
    http_response_code(404);
    exit;
}

return json_decode(<<<'JSON'
{
  "meta": {
    "title": "Germany 2036 — three possible futures",
    "baseYear": 2026,
    "targetYear": 2036,
    "defaultScenario": "pressure",
    "scenarioOrder": ["pressure", "renewal", "loss"],
    "updatedAt": "2026-07-23",
    "modelVersion": "1.1",
    "warning": "Scenarios are not forecasts. Values are modelled index ranges (2026 = 100), not euro amounts or probabilities."
  },
  "metrics": [
    {"id":"prosperity","label":"Prosperity per capita","direction":"higher","unit":"Index"},
    {"id":"income","label":"Real disposable income","direction":"higher","unit":"Index"},
    {"id":"employment","label":"Employment resilience","direction":"higher","unit":"Index"},
    {"id":"energy","label":"Energy and mobility burden","direction":"lower","unit":"Burden index"},
    {"id":"climate","label":"Climate damage and adaptation cost","direction":"lower","unit":"Burden index"},
    {"id":"state","label":"State capacity","direction":"higher","unit":"Index"}
  ],
  "strategicPrinciples": [
    {"title":"Be capable of democratic self-defence","text":"Germany must be able to protect its citizens, constitutional order and legitimate security interests, if necessary by military means and always within the Basic Law, international law, parliamentary control and its alliances. The purpose of that capability is deterrence: to make coercion and attack less attractive, not to normalise war."},
    {"title":"Trade without strategic naivety","text":"Trade and interdependence remain valuable, but ‘change through trade’ has failed as a sufficient security doctrine. Economic exchange did not reliably prevent authoritarian repression or military aggression. Europe therefore needs open trade combined with diversified suppliers, enforceable rules and protection against coercive dependencies."},
    {"title":"Renewable energy is security policy","text":"Domestic and European renewable energy, stronger grids, storage, efficiency and flexible demand reduce exposure to imported fossil fuels. They protect the economy against supply pressure and price shocks, can reduce the need for costly emergency relief, and advance climate and environmental protection at the same time. New raw-material and infrastructure dependencies still require diversification."}
  ],
  "scenarios": {
    "renewal": {
      "label":"Renewal / European sovereignty","short":"Renewal","class":"best",
      "story":"Germany and Europe decide that merely administering shortages is more expensive than acting early. Reliable investment in grids, transport, education, defence, digital infrastructure and climate adaptation begins to reinforce itself. Companies gain planning security, European cooperation reduces critical dependencies, and more people can participate in the labour market. Daily life does not become free of crises, but productivity and real household room for manoeuvre grow again because the state tackles several bottlenecks together instead of moving from emergency to emergency.",
      "premise":"Germany and Europe invest reliably, diversify critical supply chains and link climate adaptation, security, skills and technology policy.",
      "drivers":{"climate":"Prevention and adaptation limit damage; extreme events still occur.","security":"NATO remains viable while Europe builds more capability.","economy":"Energy, grids and raw-material supplies become more diversified.","technology":"More European compute, cloud and chip capacity reaches the wider economy.","society":"Labour participation, skilled migration and training soften demographic ageing."},
      "bands":{"prosperity":[108,118],"income":[106,116],"employment":[98,104],"energy":[84,98],"climate":[110,138],"state":[105,116]},
      "scores":{"prosperity":78,"income":76,"employment":72,"energySecurity":80,"technology":78,"state":74,"climateResilience":76,"social":72},
      "sliderBase":{"climateStress":-1,"renewables":2,"fragmentation":-1,"dependencies":-2,"technology":2,"productivity":2,"migration":1,"investment":2}
    },
    "pressure": {
      "label":"Adaptation under pressure — baseline","short":"Baseline","class":"medium",
      "story":"Germany remains a wealthy and fundamentally stable country, but an increasing share of its energy is spent preserving what already exists. Reforms and investment happen, usually after pressure has become visible, and they prevent a broad collapse without creating a powerful new upswing. An ageing population, defence, climate damage and industrial transformation compete for money and skilled workers. For many households, the decade therefore feels less like a dramatic crash than like prolonged stagnation: individual improvements are repeatedly absorbed by higher costs, taxes, contributions or weaker public services.",
      "premise":"Investment and reform work partly but arrive too slowly. Demography, climate impacts, defence and industrial transformation compete for scarce resources.",
      "drivers":{"climate":"Damage and adaptation cost grow together; prevention remains patchy.","security":"Alliances hold, but Europe's military and fiscal burden increases.","economy":"Diversification advances while major China, energy and raw-material risks remain.","technology":"AI lifts productivity in parts of the economy; dependencies remain high.","society":"Migration and participation soften workforce decline but do not offset it."},
      "bands":{"prosperity":[99,108],"income":[98,107],"employment":[94,101],"energy":[96,114],"climate":[126,168],"state":[94,105]},
      "scores":{"prosperity":57,"income":55,"employment":54,"energySecurity":52,"technology":55,"state":50,"climateResilience":48,"social":52},
      "sliderBase":{"climateStress":1,"renewables":1,"fragmentation":1,"dependencies":0,"technology":1,"productivity":0,"migration":0,"investment":1}
    },
    "loss": {
      "label":"Loss of capacity to act","short":"Stress case","class":"worst",
      "story":"Several manageable problems become one systemic crisis because decisions arrive late and cooperation erodes. Expensive energy, disrupted supply chains, climate damage and weak productivity accelerate industrial losses just as security and social expenditure rise. Populist-authoritarian politics turns frustration into conflict with institutions, minorities and European partners, which further weakens investment and joint action. The decisive feature is not one catastrophic event but a feedback loop: every shock leaves the state, the economy and society less able to absorb the next one.",
      "premise":"Multiple risks reinforce one another: geopolitical fragmentation, security crises, delayed infrastructure and climate adaptation, weak productivity — and democratic backsliding that reduces Germany's and Europe's ability to cooperate and act.",
      "drivers":{"climate":"Frequent extreme events meet large adaptation gaps.","security":"US retrenchment and escalation at Europe's borders are explicit stress assumptions.","economy":"Supply disruption and expensive energy accelerate industrial losses.","technology":"Dependence on non-European cloud, chip and AI infrastructure increases.","society":"Populist-authoritarian forces gain power; pressure on courts, independent media, minority rights and migrants weakens checks and social trust. EU obstruction or exit politics reduce shared capacity. Such governments may align tactically across borders, but nationalism also creates rivalry: ideological similarity does not make conflict impossible."},
      "bands":{"prosperity":[87,98],"income":[85,97],"employment":[86,96],"energy":[116,142],"climate":[158,220],"state":[78,92]},
      "scores":{"prosperity":30,"income":28,"employment":32,"energySecurity":25,"technology":27,"state":24,"climateResilience":22,"social":25},
      "sliderBase":{"climateStress":2,"renewables":-1,"fragmentation":2,"dependencies":2,"technology":-1,"productivity":-2,"migration":-1,"investment":-1}
    }
  },
  "timelineYears":[2026,2030,2033,2036],
  "households":[
    {"id":"family","label":"Two-earner family","sensitivity":{"income":1.0,"employment":0.8,"energy":0.8,"climate":0.4,"state":0.8},"daily":"Childcare, commuting, housing and contributions determine whether productivity gains reach the household.","tax":"Second-earner incentives and social contributions strongly affect additional working hours.","energyText":"Two commutes and more living space increase exposure.","housing":"Rent or financing plus renovation cost; insurance becomes more important.","transfers":"Child benefits, childcare and targeted relief work better than blanket aid.","training":"Predictable, family-compatible training makes occupational change easier.","risk":"Combined pressure from childcare gaps, mobility cost and job transformation.","help":"All-day childcare, reliable public transport, training and targeted relief."},
    {"id":"single","label":"Single person on a middle income","sensitivity":{"income":1.0,"employment":1.0,"energy":0.7,"climate":0.4,"state":0.4},"daily":"One person carries fixed housing and energy cost alone; job risk hits directly.","tax":"No second earner cushions contribution or income shocks.","energyText":"Fixed household energy cost is not shared; mobility depends on location.","housing":"Rent including heating takes a high income share, especially in cities.","transfers":"Often limited eligibility despite high fixed cost.","training":"Portable short modules help rapid sector changes.","risk":"High fixed cost amid weak wage or employment growth.","help":"Affordable housing, viable grid charges and portable training."},
    {"id":"retired","label":"Retired household","sensitivity":{"income":0.7,"employment":0.1,"energy":1.0,"climate":1.0,"state":1.1},"daily":"Pension adjustment, care, heat protection and building cost are decisive.","tax":"Health and long-term-care contributions matter more than work incentives.","energyText":"More time at home increases heating and cooling demand.","housing":"Accessibility, heat protection, renovation and insurability can be costly.","transfers":"Pension, housing support, care benefits and municipal services are central.","training":"Digital inclusion and advice replace occupational training.","risk":"Care and climate cost meet limited adaptability.","help":"Care capacity, heat protection, accessible renovation and reliable public services."},
    {"id":"industrial","label":"Industrial-worker household","sensitivity":{"income":1.0,"employment":1.3,"energy":0.8,"climate":0.4,"state":0.5},"daily":"Export demand, energy prices and technology shifts determine jobs and shift patterns.","tax":"Short-time work support, income replacement and contributions shape transitions.","energyText":"Commuting and regional car dependence increase mobility risk.","housing":"Homes and jobs are often tied to one region; value losses can reinforce each other.","transfers":"Transition aid can buy time but cannot replace a new job.","training":"Early certified skills for electrification, software and maintenance.","risk":"Structural breaks in automotive, chemical or supplier clusters.","help":"Transition training, regional investment and diversified markets."}
  ],
  "sliders":[
    {"id":"climateStress","label":"Climate and extreme-weather stress","left":"lower","right":"stronger"},
    {"id":"renewables","label":"Renewables, grids and storage","left":"stalled","right":"accelerated"},
    {"id":"fragmentation","label":"Geopolitical fragmentation","left":"cooperative","right":"hard"},
    {"id":"dependencies","label":"Critical import dependence","left":"diversified","right":"concentrated"},
    {"id":"technology","label":"European technology and AI capacity","left":"weak","right":"strong"},
    {"id":"productivity","label":"Productivity and reform effect","left":"low","right":"high"},
    {"id":"migration","label":"Labour-market integration and migration","left":"insufficient","right":"effective"},
    {"id":"investment","label":"Public investment capacity","left":"blocked","right":"reliable"}
  ],
  "influences": {
    "climateStress":{"prosperity":-1.2,"income":-0.8,"employment":-0.4,"energy":1.0,"climate":5.0,"state":-1.0},
    "renewables":{"prosperity":0.8,"income":0.5,"employment":0.3,"energy":-3.0,"climate":-1.5,"state":0.4},
    "fragmentation":{"prosperity":-1.8,"income":-1.0,"employment":-1.0,"energy":2.5,"climate":0.5,"state":-1.0},
    "dependencies":{"prosperity":-1.0,"income":-0.6,"employment":-0.8,"energy":2.0,"climate":0.3,"state":-0.6},
    "technology":{"prosperity":1.4,"income":0.8,"employment":0.4,"energy":-0.3,"climate":-0.5,"state":0.6},
    "productivity":{"prosperity":1.8,"income":1.3,"employment":0.5,"energy":-0.4,"climate":-0.4,"state":0.8},
    "migration":{"prosperity":0.8,"income":0.4,"employment":1.2,"energy":0.2,"climate":0.1,"state":0.5},
    "investment":{"prosperity":1.2,"income":0.5,"employment":0.6,"energy":-1.2,"climate":-1.2,"state":1.5}
  },
  "measures":[
    {"area":"Climate","measure":"Municipal heat, flood and sponge-city programmes","effect":"Limit damage and disruption","duration":"3–10 years","cost":"high","worst":"high","robust":true},
    {"area":"Security","measure":"Pool European procurement, air defence and civil resilience","effect":"Reduce dependence and unit cost","duration":"5–10 years","cost":"high","worst":"very high","robust":true},
    {"area":"Energy","measure":"Accelerate grids, storage, efficiency and flexible demand","effect":"Reduce price peaks and import demand","duration":"2–10 years","cost":"high","worst":"high","robust":true},
    {"area":"Technology","measure":"Open European cloud, data and AI infrastructure plus SME diffusion","effect":"Raise diffusion and sovereignty","duration":"3–8 years","cost":"medium–high","worst":"high","robust":true},
    {"area":"Labour","measure":"Scale childcare, training, recognition and integration","effect":"Improve labour supply and transitions","duration":"2–10 years","cost":"medium","worst":"high","robust":true},
    {"area":"State","measure":"Multi-year investment budgets, faster planning and impact review","effect":"Stabilise delivery capacity","duration":"1–6 years","cost":"medium","worst":"very high","robust":true}
  ],
  "citizenActions":[
    {"lever":"Make democracy work","action":"In elections, consultations, associations and citizen initiatives, ask concrete delivery questions: funding, timetable, responsibility and impact review.","supports":"State capacity and long-term investment","prevents":"Symbolic politics, polarisation and loss of trust"},
    {"lever":"Build local resilience","action":"Support or organise heat protection, unsealing, flood prevention, civil protection and neighbourhood help.","supports":"Climate resilience and social stability","prevents":"Extreme events becoming avoidable health and supply crises"},
    {"lever":"Make energy and mobility flexible","action":"Reduce consumption where it pays; combine renovation, community energy, load shifting, public transport, cycling and sharing pragmatically.","supports":"Energy security and lower import dependence","prevents":"Permanently high fixed cost and vulnerability to price shocks"},
    {"lever":"Renew your skills","action":"Regularly update digital, technical and social skills; use training rights and share knowledge at work.","supports":"Productivity, employability and technology diffusion","prevents":"Personal downward mobility during structural breaks"},
    {"lever":"Shape change at work","action":"Use works councils, professional groups or improvement processes to advance training, efficiency, secure supply chains and useful AI early.","supports":"Renewal of the industrial base","prevents":"Late, rushed adaptation and avoidable job losses"},
    {"lever":"Consume and prepare robustly","action":"Consider durability, repairability and traceable supply chains; review emergency supplies, insurance and a financial buffer appropriate to your situation.","supports":"Household and demand resilience","prevents":"Short disruptions immediately becoming personal crises"}
  ],
  "sources":[
    {"area":"Climate","kind":"official risk assessment","claim":"31 of 102 assessed climate impacts require very urgent action; adaptation needs lead time.","source":"UBA Climate Impact and Risk Assessment 2021","url":"https://www.umweltbundesamt.de/publikationen/KWRA-Zusammenfassung","use":"Constraint for all scenarios"},
    {"area":"Climate","kind":"observation","claim":"2024 was Germany's warmest year since records began in 1881.","source":"DWD Climate Status Report 2024","url":"https://www.dwd.de/DE/Home/_functions/aktuelles/2025/20250401_klimastatusbericht_2024.html","use":"Historical context, not a 2036 forecast"},
    {"area":"Demography","kind":"official projection","claim":"By 2035, the working-age population falls by 3.2–4.9 million depending on migration, or 6.2 million without net migration.","source":"Destatis, 16th coordinated population projection","url":"https://www.destatis.de/DE/Themen/Gesellschaft-Umwelt/Bevoelkerung/Bevoelkerungsvorausberechnung/annahmen_ergebnisse_16te_kBv.html","use":"Central hard range"},
    {"area":"Care","kind":"official projection","claim":"Models put the number of people needing long-term care in 2035 at roughly 5.6–6.3 million.","source":"Destatis long-term-care projection","url":"https://www.destatis.de/DE/Presse/Pressemitteilungen/2023/03/PD23_124_12.html","use":"Pressure on households, labour and the state"},
    {"area":"Economy","kind":"institutional analysis","claim":"Ageing, weak productivity and investment needs constrain potential growth; reforms can raise it.","source":"OECD Economic Survey Germany 2025","url":"https://www.oecd.org/de/publications/2025/06/oecd-economic-surveys-germany-2025_b395dc9b.html","use":"Direction only, no copied point estimate"},
    {"area":"Fiscal policy","kind":"institutional projection","claim":"Ageing raises long-run spending risks for pensions, health and long-term care.","source":"EU 2024 Ageing Report","url":"https://economy-finance.ec.europa.eu/publications/2024-ageing-report-economic-and-budgetary-projections-eu-member-states-2022-2070_en","use":"Pressure on state capacity"},
    {"area":"Energy","kind":"institutional analysis","claim":"High power prices, grid expansion and storage are central transition bottlenecks.","source":"IEA Germany 2025","url":"https://www.iea.org/reports/germany-2025","use":"Energy paths and measures"},
    {"area":"Raw materials","kind":"EU target and risk picture","claim":"2030 benchmarks: 10% extraction, 40% processing, 25% recycling; no more than 65% from one third country.","source":"EU Critical Raw Materials Act","url":"https://single-market-economy.ec.europa.eu/sectors/raw-materials/areas-specific-interest/critical-raw-materials/critical-raw-materials-act_en","use":"Diversification assumptions"},
    {"area":"Geopolitics","kind":"stress analysis","claim":"A fragmentation shock can materially reduce euro-area output and raise prices.","source":"ECB Economic Bulletin 7/2024","url":"https://www.ecb.europa.eu/press/economic-bulletin/focus/2024/html/ecb.ebbox202407_01~f5d9608296.en.html","use":"Order of magnitude for stress case only"},
    {"area":"Security","kind":"political commitment","claim":"NATO 2035 goal: 3.5% of GDP for core defence plus up to 1.5% for security and resilience.","source":"NATO Hague Summit Declaration 2025","url":"https://www.nato.int/en/about-us/official-texts-and-resources/official-texts/2025/06/25/the-hague-summit-declaration","use":"Budget competition; alliance failure remains a model stress assumption"},
    {"area":"Technology","kind":"EU stocktake","claim":"Dependence in cloud, cybersecurity and semiconductors remains substantial.","source":"EU Digital Decade 2026","url":"https://digital-strategy.ec.europa.eu/en/policies/2026-state-digital-decade-package","use":"Technology paths"},
    {"area":"Model","kind":"RealityCheck assumption","claim":"Ranges and slider effects are transparent RealityCheck model assumptions, not estimates made by the cited sources.","source":"RealityCheck scenario model","url":"#scenario-method","use":"Sensitivity model, not probability"}
  ]
}
JSON
, true, 512, JSON_THROW_ON_ERROR);
