sudo apt -y install ansible sshpass

for i in `seq -w 01 10`; do
    sshpass -p cv3m4s ssh st105@st105vm1$i.rtb-lab.pl -o StrictHostKeyChecking=no -C "/bin/true";
done

cd ansible
ansible-playbook --extra-vars "ansible_user=st105 ansible_password=cv3m4s" docker-playbook.yaml
ansible-playbook --extra-vars "ansible_user=st105 ansible_password=cv3m4s" swarm-playbook.yaml
cd ..

sudo docker service create --name registry -p 5000:5000 registry:2
sudo docker node update --label-add haproxy=true $(hostname)
sudo docker compose build
sudo docker compose push
sudo docker stack deploy --compose-file docker-compose.yml allezone 

# dockerize -wait tcp://kafka:9092 -wait web://webapp:8080
# docker network create --driver=weaveworks/net-plugin:latest_release mynetwork
