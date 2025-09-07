pipeline {
    agent any
    
    environment {
        DOCKER_IMAGE = "vulnerable-python-app"
        SONAR_PROJECT_KEY = "vulnerable-python-app"
        SNYK_TOKEN = credentials('snyk-token')
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Build') {
            steps {
                script {
                    echo "Building Docker image..."
                    sh "docker build -t ${DOCKER_IMAGE}:${BUILD_NUMBER} ."
                    sh "docker tag ${DOCKER_IMAGE}:${BUILD_NUMBER} ${DOCKER_IMAGE}:latest"
                }
            }
        }
        
        stage('SAST - SonarQube') {
            steps {
                script {
                    echo "Running SonarQube analysis..."
                    sh """
                        docker run --rm --network terraform-devsecops-network \
                        -v \$(pwd):/usr/src \
                        -e SONAR_HOST_URL=http://sonarqube:9000 \
                        -e SONAR_LOGIN=admin \
                        -e SONAR_PASSWORD=admin123 \
                        sonarsource/sonar-scanner-cli \
                        -Dsonar.projectKey=${SONAR_PROJECT_KEY} \
                        -Dsonar.sources=/usr/src \
                        -Dsonar.python.coverage.reportPaths=coverage.xml
                    """
                }
            }
        }
        
        stage('Dependency Scan - Snyk') {
            steps {
                script {
                    echo "Running Snyk dependency scan..."
                    sh """
                        docker run --rm \
                        -v \$(pwd):/project \
                        -e SNYK_TOKEN=${SNYK_TOKEN} \
                        snyk/snyk:python \
                        test --file=/project/requirements.txt --severity-threshold=high
                    """
                }
            }
        }
        
        stage('Container Scan - Trivy') {
            steps {
                script {
                    echo "Running Trivy container scan..."
                    sh """
                        docker run --rm \
                        -v /var/run/docker.sock:/var/run/docker.sock \
                        aquasec/trivy:latest image \
                        --exit-code 0 \
                        --severity HIGH,CRITICAL \
                        --format table \
                        ${DOCKER_IMAGE}:latest
                    """
                }
            }
        }
        
        stage('Deploy to Test') {
            steps {
                script {
                    echo "Deploying to test environment..."
                    sh """
                        docker stop vulnerable-app-test || true
                        docker rm vulnerable-app-test || true
                        docker run -d \
                        --name vulnerable-app-test \
                        --network terraform-devsecops-network \
                        -p 5000:5000 \
                        -e ENVIRONMENT=test \
                        ${DOCKER_IMAGE}:latest
                    """
                }
            }
        }
        
        stage('Integration Tests') {
            steps {
                script {
                    echo "Running integration tests..."
                    sh """
                        sleep 10
                        curl -f http://localhost:5000/health || exit 1
                        echo "Health check passed"
                    """
                }
            }
        }
    }
    
    post {
        always {
            echo "Pipeline completed"
            sh "docker system prune -f"
        }
        success {
            echo "Pipeline succeeded!"
        }
        failure {
            echo "Pipeline failed!"
            sh "docker logs vulnerable-app-test || true"
        }
    }
}
