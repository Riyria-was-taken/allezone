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

cd ansible

echo "Setup docker and docker swarm on all nodes:"
ansible-playbook -i ./hosts --extra-vars "ansible_user=st105 ansible_password=$1" docker-playbook.yaml
echo "Done"

echo "Start allezone:"
ansible-playbook -i ./hosts --extra-vars "ansible_user=st105 ansible_password=$1" startup-playbook.yaml
echo "Done"

cd ..
