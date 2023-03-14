# Image Time Capsule

- [Introduction](#introduction)
- [Authentication and Password Hashing](#authentication-and-password-hashing)
- [Security](#security)
- [Hosting](#hosting)
- [Automated Email](#automated-email)
- [Server Cost](#server-cost)
- [Technologies Used](#technologies-used)
- [Installation](#installation)


### Introduction
Image Time Capsule is a web application that allows authenticated users to upload images and create time capsules that are stored securely on the server. The application uses JSON Web Tokens (JWT) to authenticate users and protect resources from unauthorized access.

### Authentication and Password Hashing
Image Time Capsule uses JWT to authenticate users and allow them to perform authorized requests on protected resources. Users must first sign up and log in to the application to gain access to protected resources. Passwords are securely stored using one-way hashing to protect user data.

### Security
The application is designed with security in mind. Secure communication is established between the Relational Database Service (RDS) and Elastic Beanstalk by configuring AWS cloud security. This ensures that data transmitted between the server and the database is encrypted and secure.

### Hosting
The application is hosted on a custom domain by configuring the HTTPS protocol on Elastic Load Balancer (ELB), Certificate Manager, and DNS. This ensures that all communication between the client and the server is encrypted and secure.

### Automated Emails
The application features automated email functionality using CloudWatch, which calls a Lambda function daily at 12 am to return capsules. This allows users to receive regular updates on their time capsules and ensures that they never miss an important event.

### Server Cost
Image Time Capsule has been designed to be cost-effective, with server costs reduced by 90% by comparing costs and migrating servers from Heroku to AWS cloud services. This ensures that the application is affordable to operate and maintain.

### Technologies Used
The Image Time Capsule application uses the following technologies:

1. JWT for authentication
2. AWS cloud services (Elastic Beanstalk, RDS, ELB, Certificate Manager, Lambda, CloudWatch)
3. HTTPS protocol
4. Relational Database Service (RDS)
5. Flask


### Installation


1. Clone the repository:

git clone https://github.com/yourusername/imagetimecapsule.git

2. Navigate to the project directory:

cd imagetimecapsule

3. Install the required packages:

pip install -r requirements.txt

4. Set up the environment variables for the application


5. Set up necessary AWS tools:
- S3
- Elastic Beanstalk
- Lambda
- CloudWatch


6. Run the application

flask run

Open a web browser and navigate to http://localhost:5000 to view the application.


