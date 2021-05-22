# vdwww
VisiData on the web: [demo.visidata.org](https://demo.visidata.org/)

## Encrypted Credentials
To access the secure credentials in this repo, you will need to decrypt them.

  * Install [git-crypt](https://github.com/AGWA/git-crypt).
  * Ask your nearest friendly VisiData dev for the decryption key. It will likely be
base64 encoded for ease of communication. If the key ends with a "==" this means you can
run `base64 -d [long string of random character==]` to get the raw key.
  * Copy the raw key to a file, eg `/tmp/master/key`
  * Within the path of the repo run `git-crypt unlock /tmp/master/key`
  * You can now just use `git` as normal, all the encryption/decryption happens
automatically with hooks and filters.


## Cluster management

See `k8s/README.md`

## Deploying

Deployment to the Kubernetes cluster happens automatically after every push. During a
push CI tests are also run and deployment will not happen if there are failures. To
see the logs for the tests and deployment see the output from the Github Actions tab.

Deployments use a "rollout" strategy. If Kubernetes cannot detect that the new version
is healthy the current live containers will not be replaced. In which case either look
at the Kubernetes dashboard or use a combination of `kubectl get pods` and
`kubectl describe pod [problematic pod ID]`.
