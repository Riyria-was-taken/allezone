echo "Install ansible and sshpass..."
sudo apt -y install ansible sshpass
echo "Done"

echo "Install newest docker-compose..."
sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
export PATH=~/usr/local/bin:$PATH
docker-compose --version
echo "Done"

echo "Add other nodes to known_hosts:"
for i in `seq -w 01 10`; do
    echo "Adding st105@st105vm1$i.rtb-lab.pl..."
    sshpass -p $1 ssh st105@st105vm1$i.rtb-lab.pl -o StrictHostKeyChecking=no -C "/bin/true";
    echo "Done"
done

echo "Setup docker and docker swarm on all nodes:"
cd ansible
ansible-playbook -i ./hosts --extra-vars "ansible_user=st105 ansible_password=$1" docker-playbook.yaml
ansible-playbook -i ./hosts --extra-vars "ansible_user=st105 ansible_password=$1" swarm-playbook.yaml
cd ..
echo "Done"

echo "Create local docker registry..."
sudo docker service create --name registry -p 5000:5000 registry:2
echo "Done"

echo "Set current node as haproxy node..."
sudo docker node update --label-add haproxy=true $(hostname)
echo "Done"

#echo "Install and set up weavenet docker plugin..."
#sudo docker plugin install weaveworks/net-plugin:latest_release
#sudo docker plugin disable weaveworks/net-plugin:latest_release
#sudo docker plugin set weaveworks/net-plugin:latest_release WEAVE_MULTICAST=1
#sudo docker plugin enable weaveworks/net-plugin:latest_release
#echo "Done"

echo "Build docker services..."
sudo docker-compose build
echo "Done"

echo "Push built images to local registry..."
sudo docker-compose push
echo "Done"

echo "Deploy allezone..."
sudo docker stack deploy --compose-file docker-compose.yml allezone 
echo "Done"

