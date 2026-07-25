# Model weights

The Swin weights file is **not in Git** (120 MB — over GitHub’s 100 MB limit).

## On a new machine

Copy this file from your original laptop:

```
drive_and_act_swin_v1.pth
```

Place it in this folder (`model_swin/`).

`config.yaml` expects:

```yaml
pytorch:
  weights_path: "model_swin/drive_and_act_swin_v1.pth"
```

## Optional: Git LFS (include model in GitHub)

```bash
brew install git-lfs
git lfs install
git lfs track "*.pth"
git add .gitattributes
# Remove model_swin/*.pth from .gitignore, then:
git add model_swin/drive_and_act_swin_v1.pth
git commit -m "Add model via Git LFS"
git push
```
