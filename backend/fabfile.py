from fabric.api import *

env.user = "ubuntu"
env.key_filename = "/home/serpent/.ssh/serpent.pem"

rq_broker_hosts = ["ec2-52-60-160-109.ca-central-1.compute.amazonaws.com"]
rq_worker_hosts = [
    "ec2-52-60-134-43.ca-central-1.compute.amazonaws.com"
]


@hosts(rq_broker_hosts)
def setup_rq_broker():
    sudo("apt-get update")
    sudo("apt-get upgrade -y")

    sudo("apt-get install build-essential -y")
    sudo("apt-get install htop -y")
    sudo("apt-get install ntp ntpdate -y")

    sudo("service ntp stop")
    sudo("ln -sf /usr/share/zoneinfo/Etc/UTC /etc/localtime")
    sudo("ntpdate pool.ntp.org")
    sudo("service cron restart")

    sudo("add-apt-repository ppa:chris-lea/redis-server -y")
    sudo("apt-get update")
    sudo("apt-get install redis-server -y")

    run("curl -L https://raw.githubusercontent.com/pyenv/pyenv-installer/master/bin/pyenv-installer | bash")
    run("echo 'export PATH=\"/home/ubuntu/.pyenv/bin:$PATH\"' >> .profile")
    run("echo 'eval \"$(pyenv init -)\"' >> .profile")
    run("echo 'eval \"$(pyenv virtualenv-init -)\"' >> .profile")

    sudo("apt-get install -y libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev wget llvm libncurses5-dev libncursesw5-dev xz-utils")

    run("pyenv install 2.7.13")
    run("pyenv install 3.6.1")

    run("pyenv virtualenv 3.6.1 dashboard")
    run("pyenv local dashboard")
    run("pip install rq-dashboard")

    sudo("curl https://gist.githubusercontent.com/nbrochu/6b446ac8ce63d74a4a213b52f16c1846/raw/df9d3b6ff148d7ddaf4e65e8e01d79c0926464bc/rq-dashboard.service > /etc/systemd/system/rq-dashboard.service")

    sudo("systemctl daemon-reload")
    sudo("systemctl start rq-dashboard")
    sudo("systemctl enable rq-dashboard")


@hosts(rq_worker_hosts)
def setup_rq_worker():
    sudo("apt-get update")
    sudo("apt-get upgrade -y")

    sudo("apt-get install build-essential -y")
    sudo("apt-get install htop -y")
    sudo("apt-get install ntp ntpdate -y")

    sudo("service ntp stop")
    sudo("ln -sf /usr/share/zoneinfo/Etc/UTC /etc/localtime")
    sudo("ntpdate pool.ntp.org")
    sudo("service cron restart")

    sudo("add-apt-repository ppa:chris-lea/redis-server -y")
    sudo("apt-get update")
    sudo("apt-get install redis-server -y")

    run("curl -L https://raw.githubusercontent.com/pyenv/pyenv-installer/master/bin/pyenv-installer | bash")
    run("echo 'export PATH=\"/home/ubuntu/.pyenv/bin:$PATH\"' >> .profile")
    run("echo 'eval \"$(pyenv init -)\"' >> .profile")
    run("echo 'eval \"$(pyenv virtualenv-init -)\"' >> .profile")

    sudo("apt-get install -y libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev wget llvm libncurses5-dev libncursesw5-dev xz-utils")

    run("pyenv install 2.7.13")
    run("pyenv install 3.6.1")

    run("git clone git@github.com:SerpentAI/PlaythroughManager.git")

    run("pyenv virtualenv 3.6.1 playthrough_manager")

    sudo("apt-get install xvfb -y")

    with cd("PlaythroughManager"):
        run("pyenv local playthrough_manager")
        run("pip install -r requirements.txt")

        with cd("config"):
            run("ln -ls config.prod.yml config.yml")

    # Install supervisor
    # Setup RQ Workers in supervisor


