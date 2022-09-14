echo "Install ansible and sshpass..."
sudo apt -y install ansible sshpass
echo "Done"

echo "Add other nodes to known_hosts:"
for i in `seq -w 01 10`; do
    echo "Adding st105@st105vm1$i.rtb-lab.pl..."
    sshpass -p $1 ssh st105@st105vm1$i.rtb-lab.pl -o StrictHostKeyChecking=no -C "/bin/true";
    echo "Done"
done

echo "Setup docker and docker swarm on all nodes:"
cd ansible
ansible-playbook --extra-vars "ansible_user=st105 ansible_password=$1" docker-playbook.yaml
ansible-playbook --extra-vars "ansible_user=st105 ansible_password=$1" swarm-playbook.yaml
cd ..
echo "Done"

echo "Create local docker registry..."
sudo docker service create --name registry -p 5000:5000 registry:2
echo "Done"

echo "Set current node as haproxy node..."
sudo docker node update --label-add haproxy=true $(hostname)
echo "Done"

echo "Build docker services..."
sudo docker compose build
echo "Done"

echo "Push built images to local registry..."
sudo docker compose push
echo "Done"

echo "Deploy allezone..."
sudo docker stack deploy --compose-file docker-compose.yml allezone 
echo "Done"

# dockerize -wait tcp://kafka:9092 -wait web://webapp:8080
# docker network create --driver=weaveworks/net-plugin:latest_release mynetwork
