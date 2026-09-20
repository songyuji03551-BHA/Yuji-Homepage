---
title: Yuji Homepage
emoji: 🏒
colorFrom: purple
colorTo: yellow
sdk: docker
app_port: 3000
---

# Yuji Homepage

Personal homepage served by the Express application in `server.js`.

## Hugging Face setup

The hockey vision page optionally asks Hugging Face to caption one representative video frame. The token stays on the server and is never sent to the browser.

For local development, set the token in the shell before starting the server:

```sh
export HF_TOKEN=your_hugging_face_token
npm start
```

For a Hugging Face Space, add `HF_TOKEN` under **Settings > Repository secrets**. You can override the default image model with `HF_IMAGE_MODEL`.

## Publish without GitHub authentication

You can publish this project directly from the Hugging Face website. GitHub login and GitHub email verification are not required.

1. Open [huggingface.co/new-space](https://huggingface.co/new-space) and sign in to Hugging Face.
2. Choose a Space name, set **SDK** to `Docker`, choose the visibility you want, and create the Space.
3. Open the Space's **Files** tab, choose **Add file > Upload files**, and upload the project files.
4. Upload these files and folders from this project:
	- `Dockerfile`
	- `package.json`
	- `server.js`
	- `Homepage.html`
	- the `assets/` folder
5. Open **Settings > Variables and secrets**, choose **New secret**, and add:
	- Name: `HF_TOKEN`
	- Value: a new Hugging Face access token with inference permission
6. Optional: add the variable `HF_IMAGE_MODEL` with value `Salesforce/blip-image-captioning-base`.
7. Wait for the Space build to finish, then open the **App** tab and select **Robotics > Hockey**.
8. Upload a video and choose **Analyze video**. The browser motion scan works without the secret; the Hugging Face caption appears when `HF_TOKEN` is configured.

Do not upload `.env`, `robotics-state.json`, `uploads/`, or any token to the Space files. If the token previously appeared in a chat or public file, revoke it and create a replacement first.