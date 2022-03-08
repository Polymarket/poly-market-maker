# Poly-market-maker Deployment


This folder contains a [Terraform](https://www.terraform.io/) configuration that deploys a cluster and a container on [ECS](https://eu-west-2.console.aws.amazon.com/ecs/home?region=eu-west-2#/clusters) from an ECR image. in an [Amazon Web Services (AWS) account](http://aws.amazon.com/).

​

## Pre-requisites

​

- [Terraform](https://www.terraform.io/) installed on your computer.

​

```

brew install terraform

```

​

- An [Amazon Web Services (AWS) account](http://aws.amazon.com/).

​

## Quick start

​

**Please note that this example will deploy real resources into your AWS account.**

​

```

export AWS_ACCESS_KEY_ID=(your access key id)

export AWS_SECRET_ACCESS_KEY=(your secret access key)

```

​

Deploy the code:

​

```

terraform init

terraform apply

```

