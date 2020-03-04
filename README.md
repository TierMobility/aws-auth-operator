# aws-auth-operator

Customized User/Role Mapping from Aws to EKS

based on Kopf: https://kopf.readthedocs.io/en/latest/

# backgound information

Maps a custom resource definition to an entry in the aws-auth configmap
described here: https://docs.aws.amazon.com/eks/latest/userguide/add-user-role.html

Also logs the changes to the aws-auth configmap to stdout

# installation

- install minikube
- kubectl apply -f crds.yaml
- pipenv install
- pipenv run kopf run aws-auth.py

# testing example

- kubectl apply -f example/test.yaml
- kubectl -n kube-system get cm aws-auth -o yaml
