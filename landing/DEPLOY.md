# Deploying type-haus.com

The whole site is static. One build produces one directory; a static host serves it.

```
site/
  index.html  styles.css  404.html  favicon.svg     ->  https://type-haus.com/
  install.sh  install.ps1                           ->  curl -LsSf https://type-haus.com/install.sh | sh
  assets/*.png  robots.txt  sitemap.xml
  _headers  _redirects                              ->  host config, not served
  app/                                              ->  https://type-haus.com/app/
```

## Build

```bash
node landing/build-site.mjs      # -> ./site   (also runs the ui build with VITE_PWA_STANDALONE=1)
```

`site/` is gitignored. The script fails loudly if `site/app/` is missing the engine tarball or
the bundled Catlin house, because those only break in the browser, never at build time.

To look at the result before shipping:

```bash
python3 -m http.server 8127 --directory site
open http://127.0.0.1:8127/
```

Note that a plain static server ignores `_headers` and `_redirects`; `/app/` still works because
the directory has an `index.html`.

## Host

`_headers` and `_redirects` are the Cloudflare Pages / Netlify convention and work unmodified on
either. The CI workflow (`.github/workflows/deploy-site.yml`) is written for **Cloudflare Pages**.

### Cloudflare Pages (what CI does)

One-time, by hand in the dashboard:

1. **Pages → Create a project → Direct Upload**, name it `type-haus`. Direct Upload (rather than
   the Git integration) is deliberate: the build needs the Python engine sources and the Catlin
   house from this repo, and CI already has them.
2. **Workers & Pages → account ID** — copy it.
3. **My Profile → API Tokens → Create Token**, template *Edit Cloudflare Workers*, or a custom
   token with `Account → Cloudflare Pages → Edit`.
4. In GitHub: **Settings → Secrets and variables → Actions**, add
   `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID`.
5. **Pages project → Custom domains → Set up a domain → `type-haus.com`** (and `www` if you
   want it). If the domain's nameservers are already on Cloudflare, the DNS records and the TLS
   certificate are created for you; otherwise add the CNAME Cloudflare shows you at your
   registrar and wait for issuance.

After that, every push to `main` that touches the site redeploys it. `workflow_dispatch` runs it
on demand. Pull requests get a preview URL from the same workflow.

### Netlify (drop-in alternative)

Same artifact, same two config files, no code changes:

```bash
netlify deploy --dir=site --prod
```

or point a Netlify site at the repo with build command `node landing/build-site.mjs` and publish
directory `site`. `_headers` and `_redirects` are read from the publish directory as-is.

## What you still have to do manually

- **Own the domain.** Register `type-haus.com` (or move it) and get its nameservers onto
  Cloudflare, or be ready to add the CNAME the host gives you at your current registrar.
- **Create the host account and project**, and add the two GitHub secrets above. Nothing in the
  repo can do this for you, and CI skips the deploy step with a warning when the secrets are
  absent, so an unconfigured fork still builds green.
- **Publish `typehaus` to PyPI.** `install.sh` and `install.ps1` run
  `pipx install "typehaus[server]"`. Until the package exists on PyPI the install path fails at
  that step — the browser app at `/app/` does not depend on it.

## Caching and the service worker

Worth knowing before you debug a "why am I still seeing the old build" report:

- `/app/assets/*` is content-hashed by Vite and served `immutable` for a year.
- `/app/typehaus-engine.tar` and `/app/catlin-house.json` are **not** hashed — the same URL gets
  new bytes on every deploy. They are served `max-age=0, must-revalidate`, and the service worker
  treats them stale-while-revalidate: an installed PWA shows the cached copy instantly and picks
  the new one up on the following boot. Deploys therefore take effect one reload late for
  returning visitors, by design.
- `/app/index.html` and `/app/sw.js` are `no-cache`; navigations are network-first.

## First-load dependency

The in-browser engine downloads Pyodide from `cdn.jsdelivr.net` on first load, then caches it in
the service worker for offline use. That is the one external dependency of the deployed site —
the landing page itself has none.
