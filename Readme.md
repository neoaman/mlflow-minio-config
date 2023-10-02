# Setup Mlflow tracking server using MLflow and minio

## Step 1: Setup minio server

- Check minio official site for the available packages
    - Browsing for [linux vm](https://min.io/download#/linux)
    - ![Choose minio version](static/img/choose-minio-ubuntu.png)
- Download the appropriate version, for my case, I used an ubuntu ARM machine
    - I downloaded the file in my software directory with super user privilage
        ```sh
        cd ~/software
        wget https://dl.min.io/server/minio/release/linux-arm64/minio_20230930070229.0.0_arm64.deb
        ```
    - Then installed it in my machine
        ```
        dpkg -i minio_20230930070229.0.0_arm64.deb
        ```
- Test the minio storage
    - Check if its running properly or not, exposing the /mnt/data directory
        ```
        MINIO_ROOT_USER=admin MINIO_ROOT_PASSWORD=password minio server /mnt/data --console-address ":9001"
        ```
    - Configure nginx server for my site `minio.mlhub.in` port 80
        ```sh
        server {
            server_name minio.mlhub.in;
            #server_name 140.238.227.112;
            location / {
                proxy_pass http://localhost:9001/;
                proxy_set_header Host $host;
                proxy_set_header Upgrade $http_upgrade;
                proxy_set_header Connection upgrade;
                proxy_set_header Accept-Encoding gzip;
                # pass max_body_size 1024M; 0 for unlimited
                client_max_body_size 0;
            }
            listen 80;
            listen [::]:80;
        }
        ```
    - Run the minio and check the browser
        ```
        MINIO_ROOT_USER=admin MINIO_ROOT_PASSWORD=password minio server /mnt/data --console-address ":9001"
        ```
        ![Alt text](static/img/minio-ui-basic.png)

- Once installed, we can start the minio server using systemctl/service command
    - Upon checking status before starting the minio server
        ```sh
        sudo systemctl status minio
        # OR
        sudo service minio status
        ```
        ![Minio status](static/img/minio-status.png)
- Create minio user and group
    - Create group minio-user
        ```
        sudo groupadd -r minio-user
        sudo useradd -M -r -g minio-user minio-user
        ```
    - Create the directory if not available and give minio-user ownership
        ```
        sudo mkdir /mnt/data
        sudo chown minio-user:minio-user /min/data
        ```
    - Setup Minio environment and provide ssl certificate directory, username and password
        - We are yet to set the certs directory, will do it later
        ```
        MINIO_VOLUMES="/mnt/data"
        MINIO_OPTS="--certs-dir /home/ubuntu/.minio/certs --console-address :9001"
        MINIO_ROOT_USER=username
        MINIO_ROOT_PASSWORD=password
        ```
- Setup firewall (optional, Required for specific vm)
    - Install firewall and give public access to port 9000 and 9001
        ```sh
        sudo apt install firewalld
        sudo firewall-cmd --zone=public --permanent --add-port=80/tcp
        sudo firewall-cmd --zone=public --permanent --add-port=9000/tcp
        sudo firewall-cmd --zone=public --permanent --add-port=9001/tcp
        sudo firewall-cmd --reload
        ```
- Install certgen from official minio github repository
    - Check the site https://github.com/minio/certgen and choose appropriate version
        - In my case I am using ubuntu ARM machine
        ![Check certgen available package](static/img/check-certgen-pkg.png)
    - Download the package in your software (any prefered) directory and install
        - In my case the url was https://github.com/minio/certgen/releases/download/v1.2.1/certgen_1.2.1_linux_arm64.deb
        ```sh
        cd /home/ubuntu/software
        wget https://github.com/minio/certgen/releases/download/v1.2.1/certgen_1.2.1_linux_arm64.deb
        dpkg -i certgen_1.2.1_linux_arm64.deb        
        ```
- Generate certificate in `/home/ubuntu/.minio/cert` directory
    - I have many subdomains so I will generate an wildcard certificate, applicable to all my sub-domains
        If you want to access using IP address, use ip instead
        ```sh
        sudo certgen -host *.mlhub.in
        ```
    - It will generate 2 files private.key and public.crt, and minio also look for exactly these files
        - Will provide ownership of this two files to minio-user
        ```sh
        sudo chown minio-user:minio-user /home/ubuntu/.minio/certs/private.key
        sudo chown minio-user:minio-user /home/ubuntu/.minio/certs/public.crt
        ```
- Start the minio server
    - Using the systemctl/service command we need to enable and start the minio server
        ```sh
        sudo systemctl enable minio # OR sudo service minio enable 
        sudo systemctl start minio # OR sudo service minio start
        sudo systemctl status minio # OR sudo service minio status
        ```
        ![Minio Status](static/img/minio-server-status-running.png) 

- Expose the site using nginx
    - Looking at the server, we can see 2 ports, One for console exposed to port 9001 and one S3-API exposed to port 9000
    - Need to update the nginx config
        - Added one file minio-server in sites-available i.e. `/etc/nginx/sites-available/minio-server`
        ```sh
        server {
            server_name minio.mlhub.in;
            #server_name 140.238.227.112;
            location / {
                proxy_pass https://127.0.0.1:9001/;
                proxy_set_header Host $host;
                proxy_set_header Upgrade $http_upgrade;
                proxy_set_header Connection upgrade;
                proxy_set_header Accept-Encoding gzip;
                client_max_body_size 0;
            }
            listen 80;
            listen [::]:80;
        }
        server {
            server_name s3.mlhub.in;
            #server_name 140.238.227.112;
            location / {
                proxy_pass https://127.0.0.1:9000/;
                proxy_set_header Host $host;
                proxy_set_header Upgrade $http_upgrade;
                proxy_set_header Connection upgrade;
                proxy_set_header Accept-Encoding gzip;
                client_max_body_size 0;
            }
            listen 80;
            listen [::]:80;
        }
        ```
        - Above first server configuration is for minio console and second is for the S3-API
    - Create a symbolic link of our configuration file in sites-enabled directory
        ```sh
        sudo ln -s /etc/nginx/sites-available/minio-server /etc/nginx/sites-enabled/
        ```
    - Restart the nginx server using systemctl/service
        ```sh
        sudo service nginx restart
        # OR
        sudo systemctl restart nginx
        ```

- Get the ssl certificate using certbot/letsencrypt
    - Give it a try, running `certbot`
    - It will ask you for the subdomains in a list
    - Choose one and repeat for others

- Test if the S3-API is working or not
    - Lets open our minio site (in my case https://minio.mlhub.in)
    - Generate new Access key (id and secret)
    ![Generate new access key secret](static/img/generate-minio-access-key-secret.png)
    - Create bicket and upload some files
    - Open notebook and check for the file through boto3
    ![Check access through boto3](static/img/check-access-through-boto3.png)
    
