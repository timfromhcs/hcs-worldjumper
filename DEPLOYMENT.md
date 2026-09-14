# Deployment Guide

## Hugging Face Spaces
HCS WorldJumper is configured as a Static Space:
* Repository: `https://huggingface.co/spaces/timfromhcs/hcs-worldjumper`
* SDK: `static`
* Entry Point: `index.html`
* Configuration: Frontmatter in `README.md`
* Automated deployment via `python src/deploy_hf.py` using `HF_TOKEN`.

## GitHub Repository & CI/CD
* Repository: `https://github.com/timfromhcs/hcs-worldjumper`
* CI/CD: `.github/workflows/ci.yml` validates manifests, release checksums, and JavaScript modules on push.
* Token: Authenticated via `GITHUB_TOKEN` from `.env`.
