pipeline {
    agent any

    environment {
        AWS_REGION = 'ap-south-1'

        ECR_REGISTRY = '308621094314.dkr.ecr.ap-south-1.amazonaws.com'

        AGENT_IMAGE   = "${ECR_REGISTRY}/cloudpack-agent-service"
        WEATHER_IMAGE = "${ECR_REGISTRY}/cloudpack-weather-service"
        MEMORY_IMAGE  = "${ECR_REGISTRY}/cloudpack-memory-service"
        GATEWAY_IMAGE = "${ECR_REGISTRY}/cloudpack-api-gateway"
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Test') {
    steps {
        echo 'Running CloudPack environment checks...'
        bat '''
            docker --version
            kubectl version --client
            "C:\\Users\\dogra\\AppData\\Local\\Programs\\Amazon\\AWSCLIV2\\aws.exe" --version
            echo CloudPack environment checks completed.
        '''
    }
}

        stage('Build Docker Images') {
            steps {
                bat '''
                    docker build -t %AGENT_IMAGE%:latest ./agent-service
                    docker build -t %WEATHER_IMAGE%:latest ./weather-service
                    docker build -t %MEMORY_IMAGE%:latest ./memory-service
                    docker build -t %GATEWAY_IMAGE%:latest ./api-gateway
                '''
            }
        }

        stage('Login to Amazon ECR') {
            steps {
                bat '''
                    aws ecr get-login-password --region %AWS_REGION% | docker login --username AWS --password-stdin %ECR_REGISTRY%
                '''
            }
        }

        stage('Push Images to ECR') {
            steps {
                bat '''
                    docker push %AGENT_IMAGE%:latest
                    docker push %WEATHER_IMAGE%:latest
                    docker push %MEMORY_IMAGE%:latest
                    docker push %GATEWAY_IMAGE%:latest
                '''
            }
        }

        stage('Configure Kubernetes') {
            steps {
                bat '''
                    aws eks update-kubeconfig --region %AWS_REGION% --name cloudpack-eks
                    kubectl get nodes
                '''
            }
        }

        stage('Create Kubernetes Secret') {
    steps {
        withCredentials([
            string(credentialsId: 'GROQ_API_KEY', variable: 'GROQ_API_KEY'),
            string(credentialsId: 'OPENWEATHER_API_KEY', variable: 'OPENWEATHER_API_KEY')
        ]) {
            bat '''
                kubectl create secret generic cloudpack-secrets ^
                  --namespace cloudpack ^
                  --from-literal=GROQ_API_KEY="%GROQ_API_KEY%" ^
                  --from-literal=OPENWEATHER_API_KEY="%OPENWEATHER_API_KEY%" ^
                  --dry-run=client -o yaml | kubectl apply -f -
            '''
        }
    }
}

        stage('Deploy to Kubernetes') {
            steps {
                bat '''
                    kubectl apply -f k8s/namespace.yaml
                    kubectl apply -f k8s/configmap.yaml

                    kubectl apply -f k8s/weather-deployment.yaml
                    kubectl apply -f k8s/weather-service.yaml

                    kubectl apply -f k8s/memory-deployment.yaml
                    kubectl apply -f k8s/memory-service.yaml

                    kubectl apply -f k8s/agent-deployment.yaml
                    kubectl apply -f k8s/agent-service.yaml

                    kubectl apply -f k8s/gateway-deployment.yaml
                    kubectl apply -f k8s/gateway-service.yaml
                '''
            }
        }

        stage('Verify Deployment') {
            steps {
                bat '''
                    kubectl get pods -n cloudpack
                    kubectl get services -n cloudpack
                '''
            }
        }
    }

    post {
        success {
            echo 'CloudPack CI/CD pipeline completed successfully!'
        }

        failure {
            echo 'CloudPack CI/CD pipeline failed.'
        }
    }
}