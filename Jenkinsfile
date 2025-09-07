pipeline {
    agent any
    
    environment {
        DOCKER_IMAGE = "vulnerable-python-app"
        SONAR_PROJECT_KEY = "vulnerable-python-app"
        // Use Docker TCP connection for cross-platform compatibility
//        DOCKER_HOST = "tcp://host.docker.internal:2375"
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
                echo "Code checked out successfully"
            }
        }
        
        stage('Build') {
            steps {
                script {
                    echo "Building Docker image..."
                    echo "Using Docker host: ${env.DOCKER_HOST}"
                    sh "docker build -t ${DOCKER_IMAGE}:${BUILD_NUMBER} ."
                    sh "docker tag ${DOCKER_IMAGE}:${BUILD_NUMBER} ${DOCKER_IMAGE}:latest"
                    echo "Docker image built successfully"
                }
            }
        }
       

stage('SAST - SonarQube') {
    steps {
        script {
            echo "Running SonarQube analysis..."
            withCredentials([string(credentialsId: 'sonarqube-token', variable: 'SONAR_TOKEN')]) {
                sh """
                    docker run --rm --network terraform-devsecops-network \
                    -v \$(pwd):/usr/src \
                    -e SONAR_HOST_URL=http://sonarqube-devsecops:9000 \
                    -e SONAR_TOKEN=\${SONAR_TOKEN} \
                    sonarsource/sonar-scanner-cli \
                    -Dsonar.projectKey=${SONAR_PROJECT_KEY} \
                    -Dsonar.sources=/usr/src \
                    -Dsonar.exclusions=**/*.pyc,**/migrations/**,**/venv/**
                """
            }
        }
    }
}
 
        stage('Dependency Scan - Snyk') {
            when {
                expression { 
                    try {
                        env.SNYK_TOKEN = credentials('snyk-token')
                        return true
                    } catch (Exception e) {
                        echo "Snyk token not configured, skipping dependency scan"
                        return false
                    }
                }
            }
            steps {
                script {
                    echo "Running Snyk dependency scan..."
                    withCredentials([string(credentialsId: 'snyk-token', variable: 'SNYK_TOKEN')]) {
                        sh """
                            docker run --rm \
                            -v \$(pwd):/project \
                            -e SNYK_TOKEN=\${SNYK_TOKEN} \
                            snyk/snyk:python \
                            test --file=/project/requirements.txt --severity-threshold=medium || true
                        """
                    }
                }
            }
        }
        
        stage('Container Scan - Trivy') {
            steps {
                script {
                    echo "Running Trivy container scan..."
                    sh """
                        docker run --rm \
                        -e DOCKER_HOST=${env.DOCKER_HOST} \
                        --add-host=host.docker.internal:host-gateway \
                        aquasec/trivy:latest image \
                        --exit-code 0 \
                        --severity HIGH,CRITICAL \
                        --format table \
                        ${DOCKER_IMAGE}:latest || true
                    """
                }
            }
        }
        
        stage('Deploy to Test') {
            steps {
                script {
                    echo "Deploying to test environment..."
                    sh """
                        docker stop vulnerable-app-test 2>/dev/null || true
                        docker rm vulnerable-app-test 2>/dev/null || true
                        
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
                        sleep 15
                        curl -f http://localhost:5000/health || exit 1
                        echo "Health check passed"
                        curl -f http://localhost:5000/ || exit 1
                        echo "Basic functionality test passed"
                    """
                }
            }
        }
    }
    
    post {
        always {
            script {
                echo "Pipeline completed"
                sh """
                    docker system prune -f || true
                    echo "Cleanup completed"
                """
            }
        }
        success {
            echo "Pipeline succeeded!"
        }
        failure {
            script {
                echo "Pipeline failed!"
                sh """
                    echo "=== Container logs for debugging ==="
                    docker logs vulnerable-app-test 2>/dev/null || echo "No test container logs available"
                """
            }
        }
    }
}
