pipeline {
    agent any
    
    environment {
        SNYK_TOKEN = credentials('snyk-api-token')
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
                    # Check if Snyk is installed
                    if command -v snyk &> /dev/null; then
                        echo "Snyk CLI is already installed"
                    else
                        echo "Installing Snyk CLI..."
                        curl -Lo ./snyk https://static.snyk.io/cli/latest/snyk-linux
                        chmod +x ./snyk
                        sudo mv ./snyk /usr/local/bin/
                    fi
                    
                    # Authenticate with Snyk
                    snyk auth ${SNYK_TOKEN}
                '''
            }
        }
        
        stage('Build Docker Image') {
            steps {
                sh '''
                    echo "Building Docker image..."
                    docker build -t ${DOCKER_IMAGE}:${DOCKER_TAG} .
                    docker tag ${DOCKER_IMAGE}:${DOCKER_TAG} ${DOCKER_IMAGE}:latest
                '''
            }
        }
        
        stage('Run Unit Tests') {
            steps {
                sh '''
                    echo "Running unit tests..."
                    docker run --rm ${DOCKER_IMAGE}:${DOCKER_TAG} python test_app.py
                '''
            }
        }
        
        stage('Snyk Security Scan - Dependencies') {
            steps {
                script {
                    sh '''
                        echo "Scanning Python dependencies..."
                        # Create reports directory
                        mkdir -p reports
                        
                        # Run Snyk test and capture results
                        snyk test --file=requirements.txt --json > reports/snyk-deps-report.json || true
                        
                        # Display summary
                        echo "=== Dependency Scan Results ==="
                        snyk test --file=requirements.txt || true
                    '''
                    
                    // Check if critical vulnerabilities exist
                    def hasVulnerabilities = sh(
                        script: 'grep -q "\\"severity\\":\\"critical\\"" reports/snyk-deps-report.json',
                        returnStatus: true
                    )
                    
                    if (hasVulnerabilities == 0) {
                        currentBuild.result = 'UNSTABLE'
                        echo "WARNING: Critical vulnerabilities found in dependencies"
                    }
                }
            }
        }
        
        stage('Snyk Security Scan - Docker Image') {
            steps {
                script {
                    sh '''
                        echo "Scanning Docker image..."
                        # Scan container and save results
                        snyk container test ${DOCKER_IMAGE}:${DOCKER_TAG} --json > reports/snyk-container-report.json || true
                        
                        # Display summary
                        echo "=== Container Scan Results ==="
                        snyk container test ${DOCKER_IMAGE}:${DOCKER_TAG} || true
                    '''
                    
                    // Mark build as unstable if vulnerabilities found
                    def hasVulnerabilities = sh(
                        script: 'test -s reports/snyk-container-report.json && grep -q "vulnerabilities" reports/snyk-container-report.json',
                        returnStatus: true
                    )
                    
                    if (hasVulnerabilities == 0) {
                        currentBuild.result = 'UNSTABLE'
                        echo "WARNING: Vulnerabilities found in container image"
                    }
                }
            }
        }
        
        stage('Snyk Code Analysis') {
            steps {
                script {
                    sh '''
                        echo "Running static code analysis..."
                        # Run code analysis
                        snyk code test --json > reports/snyk-code-report.json || true
                        
                        # Display summary
                        echo "=== Code Analysis Results ==="
                        snyk code test || true
                    '''
                    
                    // Check for code issues
                    def hasIssues = sh(
                        script: 'test -s reports/snyk-code-report.json',
                        returnStatus: true
                    )
                    
                    if (hasIssues == 0) {
                        echo "Code quality issues detected"
                    }
                }
            }
        }
        
        stage('Generate Security Report') {
            steps {
                sh '''
                    echo "Generating consolidated security report..."
                    
                    # Create summary report
                    cat > reports/security-summary.txt << EOF
=== Security Scan Summary ===
Build Number: ${BUILD_NUMBER}
Date: $(date)
Image: ${DOCKER_IMAGE}:${DOCKER_TAG}

EOF
                    
                    # Add dependency vulnerabilities count
                    if [ -f reports/snyk-deps-report.json ]; then
                        echo "## Dependency Vulnerabilities:" >> reports/security-summary.txt
                        echo "Total: $(grep -o '"severity"' reports/snyk-deps-report.json | wc -l)" >> reports/security-summary.txt
                        echo "Critical: $(grep -o '"severity":"critical"' reports/snyk-deps-report.json | wc -l)" >> reports/security-summary.txt
                        echo "High: $(grep -o '"severity":"high"' reports/snyk-deps-report.json | wc -l)" >> reports/security-summary.txt
                        echo "Medium: $(grep -o '"severity":"medium"' reports/snyk-deps-report.json | wc -l)" >> reports/security-summary.txt
                        echo "Low: $(grep -o '"severity":"low"' reports/snyk-deps-report.json | wc -l)" >> reports/security-summary.txt
                        echo "" >> reports/security-summary.txt
                    fi
                    
                    # Add container vulnerabilities count
                    if [ -f reports/snyk-container-report.json ]; then
                        echo "## Container Vulnerabilities:" >> reports/security-summary.txt
                        echo "Total: $(grep -o '"severity"' reports/snyk-container-report.json | wc -l)" >> reports/security-summary.txt
                        echo "" >> reports/security-summary.txt
                    fi
                    
                    # Add code issues count
                    if [ -f reports/snyk-code-report.json ]; then
                        echo "## Code Issues:" >> reports/security-summary.txt
                        echo "Total: $(grep -o '"issue"' reports/snyk-code-report.json | wc -l)" >> reports/security-summary.txt
                        echo "" >> reports/security-summary.txt
                    fi
                    
                    # Display the summary
                    cat reports/security-summary.txt
                '''
            }
        }
        
        stage('Archive Reports') {
            steps {
                archiveArtifacts artifacts: 'reports/**/*', allowEmptyArchive: true
                
                // Publish HTML reports if HTML Publisher plugin is installed
                script {
                    if (fileExists('reports/security-summary.txt')) {
                        echo "Security reports have been archived"
                    }
                }
            }
        }
    }
    
    post {
        always {
            // Clean up Docker images to save space
            sh '''
                echo "Cleaning up Docker images..."
                docker rmi ${DOCKER_IMAGE}:${DOCKER_TAG} || true
            '''
        }
        success {
            echo 'Pipeline completed successfully!'
        }
        unstable {
            echo 'Pipeline completed with warnings. Security vulnerabilities detected!'
            echo 'Review the security reports in the archived artifacts.'
        }
        failure {
            echo 'Pipeline failed. Check the logs for details.'
        }
    }
}
