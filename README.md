# aws-auth-operator

based on Kopf: https://kopf.readthedocs.io/en/latest/

# backgound information

AWS Auth - https://docs.aws.amazon.com/eks/latest/userguide/add-user-role.html

# installation

- install minikube
- kubectl apply -f crds.yaml
- pipenv install
- pipenv run kopf run aws-auth.py

# testing 

- kubectl apply -f test.yaml
- kubectl -n kube-system get cm aws-auth -o yaml
