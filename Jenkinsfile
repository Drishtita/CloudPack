
pipeline {
    agent any

    options {
        timestamps()
    }

    stages {

        stage('Checkout') {
            steps {
                echo 'Checking out CloudPack source code...'
                checkout scm
            }
        }

        stage('Test Environment') {
            steps {
                echo 'Checking CloudPack build environment...'

                bat '''
                    docker --version
                    kubectl version --client
                    "C:\\Users\\dogra\\AppData\\Local\\Programs\\Amazon\\AWSCLIV2\\aws.exe" --version
                    echo Environment checks completed successfully.
                '''
            }
        }

        stage('Build Docker Images') {
            steps {
                echo 'Building CloudPack Docker images...'

                bat '''
                    docker build -t cloudpack-weather-service:latest ./weather-service
                    docker build -t cloudpack-memory-service:latest ./memory-service
                    docker build -t cloudpack-agent-service:latest ./agent-service
                    docker build -t cloudpack-api-gateway:latest ./api-gateway
                '''
            }
        }
    }

    post {
        success {
            echo 'CloudPack CI Pipeline completed successfully!'
            echo 'All Docker images were built successfully.'
        }

        failure {
            echo 'CloudPack CI Pipeline failed. Check the Jenkins console output.'
        }

        always {
            echo 'Jenkins pipeline execution finished.'
        }
    }
}
```