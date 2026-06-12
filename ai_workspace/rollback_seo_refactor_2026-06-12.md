# Rollback: SEO / Landing Page Refactor

Date: 2026-06-12

## Changed files

- [index.html](../index.html)
- [about.html](../about.html)
- [style.css](../style.css)
- [\.htaccess](../.htaccess)

## Immediate rollback

If you want to undo all changes from this refactor in one step, run this from the repository root:

```powershell
git restore index.html about.html style.css .htaccess
```

## Partial rollback

- To revert only the landing page change, restore [index.html](../index.html) and [style.css](../style.css).
- To revert only the server-side changes, restore [\.htaccess](../.htaccess).
- To revert only the document-structure fix, restore [about.html](../about.html).

## Notes

- The rollback is safe because the change set is limited to static HTML, CSS, and Apache rules.
- No data files or generated KPI datasets were modified.