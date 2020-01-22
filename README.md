# aws-auth-operator

based on Kopf: https://kopf.readthedocs.io/en/latest/

# installation

- install minikube
- kubectl apply -f crds.yaml
- pipenv install
- pipenv run kopf run aws-auth.py

# testing 

- kubectl apply -f test.yaml
- kubectl -n kube-system get cm aws-auth -o yaml