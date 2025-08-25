pipeline {
    agent any
    
    environment {
        SNYK_TOKEN = credentials('snyk-token')
        DOCKER_IMAGE = 'vulnerable-python-app'
        DOCKER_TAG = "${BUILD_NUMBER}"
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Setup Snyk') {
            steps {
                sh '''
                    # Install Snyk CLI if not present
                    if ! command -v snyk &> /dev/null; then
                        echo "Installing Snyk CLI..."
                        curl -Lo snyk https://static.snyk.io/cli/latest/snyk-linux
                        chmod +x snyk
                        mv snyk /usr/local/bin/
                    fi
                    
                    # Authenticate with Snyk
                    snyk auth ${SNYK_TOKEN}
                '''
            }
        }
        
        stage('Build Docker Image') {
            steps {
                script {
                    docker.build("${DOCKER_IMAGE}:${DOCKER_TAG}")
                }
            }
        }
        
        stage('Run Unit Tests') {
            steps {
                sh '''
                    docker run --rm ${DOCKER_IMAGE}:${DOCKER_TAG} python test_app.py
                '''
            }
        }
        
        stage('Snyk Security Scan - Dependencies') {
            steps {
                script {
                    try {
                        sh '''
                            echo "Scanning Python dependencies..."
                            snyk test --file=requirements.txt --severity-threshold=high --json > snyk-deps-report.json || true
                            snyk test --file=requirements.txt --severity-threshold=high
                        '''
                    } catch (Exception e) {
                        echo "Vulnerabilities found in dependencies. Check the report."
                        currentBuild.result = 'UNSTABLE'
                    }
                }
            }
        }
        
        stage('Snyk Security Scan - Docker Image') {
            steps {
                script {
                    try {
                        sh '''
                            echo "Scanning Docker image..."
                            snyk container test ${DOCKER_IMAGE}:${DOCKER_TAG} --severity-threshold=high --json > snyk-container-report.json || true
                            snyk container test ${DOCKER_IMAGE}:${DOCKER_TAG} --severity-threshold=high
                        '''
                    } catch (Exception e) {
                        echo "Vulnerabilities found in container. Check the report."
                        currentBuild.result = 'UNSTABLE'
                    }
                }
            }
        }
        
        stage('Snyk Code Analysis') {
            steps {
                script {
                    try {
                        sh '''
                            echo "Running static code analysis..."
                            snyk code test --severity-threshold=high --json > snyk-code-report.json || true
                            snyk code test --severity-threshold=high
                        '''
                    } catch (Exception e) {
                        echo "Code quality issues found. Check the report."
                        currentBuild.result = 'UNSTABLE'
                    }
                }
            }
        }
        
        stage('Generate Security Report') {
            steps {
                sh '''
                    echo "=== Security Scan Summary ===" > security-report.txt
                    echo "" >> security-report.txt
                    
                    if [ -f snyk-deps-report.json ]; then
                        echo "Dependencies Vulnerabilities:" >> security-report.txt
                        cat snyk-deps-report.json | jq '.vulnerabilities | length' >> security-report.txt
                        echo "" >> security-report.txt
                    fi
                    
                    if [ -f snyk-container-report.json ]; then
                        echo "Container Vulnerabilities:" >> security-report.txt
                        cat snyk-container-report.json | jq '.vulnerabilities | length' >> security-report.txt
                        echo "" >> security-report.txt
                    fi
                    
                    if [ -f snyk-code-report.json ]; then
                        echo "Code Issues:" >> security-report.txt
                        cat snyk-code-report.json | jq '.runs[0].results | length' >> security-report.txt
                    fi
                    
                    cat security-report.txt
                '''
            }
        }
        
        stage('Archive Reports') {
            steps {
                archiveArtifacts artifacts: '*.json,*.txt', allowEmptyArchive: true
            }
        }
    }
    
    post {
        always {
            cleanWs()
        }
        success {
            echo 'Pipeline completed successfully!'
        }
        unstable {
            echo 'Pipeline completed with warnings. Review security reports.'
        }
        failure {
            echo 'Pipeline failed. Check the logs for details.'
        }
    }
}
