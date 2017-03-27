from fabric.api import *

env.user = "ubuntu"
env.key_filename = "/home/serpent/.ssh/serpent.pem"


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
    sudo("sudo sed -i 's/bind 127.0.0.1/bind 0.0.0.0/' /etc/redis/redis.conf")
    sudo("systemctl restart redis")

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


@parallel(pool_size=10)
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

    run("pyenv virtualenv 3.6.1 playthrough_manager")

    run("git clone https://github.com/SerpentAI/PlaythroughManager.git")

    sudo("apt-get install xvfb -y")
    sudo("apt-get install chromium-browser -y")

    with cd("PlaythroughManager/backend"):
        run("pyenv local playthrough_manager")
        run("pip install -r requirements.txt")

        with cd("config"):
            run("ln -s config.prod.yml config.yml")

    run("pyenv virtualenv 2.7.13 supervisor")
    run("pyenv local supervisor")
    run("pip install supervisor")

    sudo("echo_supervisord_conf > /etc/supervisord.conf")
    sudo("chown ubuntu:ubuntu /etc/supervisord.conf")

    run("curl https://gist.githubusercontent.com/nbrochu/017cea2ccbf20a4935cf7176b7a293bc/raw/a9df55372c009f500005212030af8756cde4857d/supervisor-program.conf >> /etc/supervisord.conf")

    sudo("mkdir /var/log/PlaythroughManager")
    sudo("chown -R ubuntu:ubuntu /var/log/PlaythroughManager")

    run("supervisord")
