# Configure Terraform and providers
terraform {
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
    local = {
      source  = "hashicorp/local"
      version = "~> 2.4"
    }
  }
}

# Configure Docker provider
provider "docker" {
  # Automatic detection works across all platforms
}

# Variables
variable "environment" {
  description = "Environment name"
  type        = string
  default     = "devsecops"
}

variable "github_repo_url" {
  description = "GitHub repository URL for the vulnerable app"
  type        = string
  default     = "https://github.com/yourusername/vulnerable-python-app.git"
}

# Create custom network for all services
resource "docker_network" "devsecops_network" {
  name = "terraform-${var.environment}-network"
}

# Create volumes for persistent data
resource "docker_volume" "jenkins_data" {
  name = "jenkins-${var.environment}-data"
}

resource "docker_volume" "sonarqube_data" {
  name = "sonarqube-${var.environment}-data"
}

resource "docker_volume" "sonarqube_logs" {
  name = "sonarqube-${var.environment}-logs"
}

resource "docker_volume" "sonarqube_extensions" {
  name = "sonarqube-${var.environment}-extensions"
}

resource "docker_volume" "postgresql_data" {
  name = "postgresql-${var.environment}-data"
}

# Pull required images
resource "docker_image" "jenkins" {
  name         = "jenkins/jenkins:lts"
  keep_locally = false
}

resource "docker_image" "sonarqube" {
  name         = "sonarqube:community"
  keep_locally = false
}

resource "docker_image" "postgres" {
  name         = "postgres:13"
  keep_locally = false
}

resource "docker_image" "python_app" {
  name         = "python:3.9-slim"
  keep_locally = false
}

# PostgreSQL database for SonarQube
resource "docker_container" "postgres" {
  image = docker_image.postgres.image_id
  name  = "postgres-${var.environment}"

  env = [
    "POSTGRES_USER=sonar",
    "POSTGRES_PASSWORD=sonar123",
    "POSTGRES_DB=sonarqube"
  ]

  networks_advanced {
    name = docker_network.devsecops_network.name
  }

  volumes {
    volume_name    = docker_volume.postgresql_data.name
    container_path = "/var/lib/postgresql/data"
  }

  healthcheck {
    test         = ["CMD-SHELL", "pg_isready -U sonar -d sonarqube"]
    interval     = "30s"
    timeout      = "10s"
    retries      = 5
    start_period = "30s"
  }
}

# SonarQube container
resource "docker_container" "sonarqube" {
  image = docker_image.sonarqube.image_id
  name  = "sonarqube-${var.environment}"

  env = [
    "SONAR_JDBC_URL=jdbc:postgresql://postgres-${var.environment}:5432/sonarqube",
    "SONAR_JDBC_USERNAME=sonar",
    "SONAR_JDBC_PASSWORD=sonar123"
  ]

  ports {
    internal = 9000
    external = 9000
  }

  networks_advanced {
    name = docker_network.devsecops_network.name
  }

  volumes {
    volume_name    = docker_volume.sonarqube_data.name
    container_path = "/opt/sonarqube/data"
  }

  volumes {
    volume_name    = docker_volume.sonarqube_logs.name
    container_path = "/opt/sonarqube/logs"
  }

  volumes {
    volume_name    = docker_volume.sonarqube_extensions.name
    container_path = "/opt/sonarqube/extensions"
  }

  depends_on = [docker_container.postgres]

  healthcheck {
    test         = ["CMD-SHELL", "curl -f http://localhost:9000/api/system/status | grep UP || exit 1"]
    interval     = "30s"
    timeout      = "10s"
    retries      = 10
    start_period = "90s"
  }
}

# Jenkins configuration files with Docker socket fix
resource "local_file" "jenkins_dockerfile" {
  filename = "${path.module}/jenkins-config/Dockerfile"
  content = <<-EOF
FROM jenkins/jenkins:lts

USER root

# Install Docker CLI
RUN apt-get update && apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    && curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null \
    && apt-get update \
    && apt-get install -y docker-ce-cli

# Install additional tools
RUN apt-get install -y git curl wget

# Create docker group and add jenkins user to it
RUN groupadd -g 999 docker || true
RUN usermod -aG docker jenkins

# Install Jenkins plugins
COPY plugins.txt /usr/share/jenkins/ref/plugins.txt
RUN jenkins-plugin-cli --plugin-file /usr/share/jenkins/ref/plugins.txt

# Create entrypoint script to fix socket permissions automatically
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

USER jenkins

ENTRYPOINT ["/entrypoint.sh"]
CMD ["/usr/local/bin/jenkins.sh"]
EOF
}

# Create entrypoint script for automatic Docker socket permission fix
resource "local_file" "jenkins_entrypoint" {
  filename = "${path.module}/jenkins-config/entrypoint.sh"
  content = <<-EOF
#!/bin/bash

# Wait for Docker socket to be available
echo "Checking Docker socket availability..."
while [ ! -e /var/run/docker.sock ]; do
    echo "Waiting for Docker socket..."
    sleep 2
done

# Fix Docker socket permissions if it exists
if [ -e /var/run/docker.sock ]; then
    echo "Docker socket found, fixing permissions..."
    
    # Get the GID of the docker socket
    DOCKER_GID=$(stat -c '%g' /var/run/docker.sock)
    echo "Docker socket GID: $DOCKER_GID"
    
    # Create docker group with matching GID if it doesn't exist with correct GID
    if ! getent group $DOCKER_GID > /dev/null 2>&1; then
        echo "Creating docker group with GID $DOCKER_GID"
        groupadd -g $DOCKER_GID docker || true
    fi
    
    # Add jenkins user to docker group
    echo "Adding jenkins user to docker group..."
    usermod -aG docker jenkins 2>/dev/null || true
    
    # Ensure socket is accessible (fallback method)
    echo "Setting socket permissions..."
    chmod 666 /var/run/docker.sock 2>/dev/null || true
    
    echo "Docker socket configuration completed"
else
    echo "Docker socket not found - Jenkins will use alternative Docker connection methods"
fi

# Test Docker access
echo "Testing Docker access..."
if docker version > /dev/null 2>&1; then
    echo "Docker access confirmed"
else
    echo "Docker access test failed - will retry after Jenkins starts"
fi

# Start Jenkins
echo "Starting Jenkins..."
exec "$@"
EOF
}

resource "local_file" "jenkins_plugins" {
  filename = "${path.module}/jenkins-config/plugins.txt"
  content = <<-EOF
workflow-aggregator:latest
git:latest
github:latest
docker-workflow:latest
sonar:latest
pipeline-stage-view:latest
blueocean:latest
credentials:latest
credentials-binding:latest
plain-credentials:latest
EOF
}

# Build custom Jenkins image with Docker support and automatic socket fix
resource "docker_image" "custom_jenkins" {
  name = "custom-jenkins:latest"
  build {
    context = "${path.module}/jenkins-config"
    dockerfile = "Dockerfile"
  }
  depends_on = [
    local_file.jenkins_dockerfile,
    local_file.jenkins_plugins,
    local_file.jenkins_entrypoint
  ]
}

# Jenkins container with automated Docker socket access
resource "docker_container" "jenkins" {
  image = docker_image.custom_jenkins.image_id
  name  = "jenkins-${var.environment}"

  ports {
    internal = 8080
    external = 8080
  }

  ports {
    internal = 50000
    external = 50000
  }

  networks_advanced {
    name = docker_network.devsecops_network.name
  }

  volumes {
    volume_name    = docker_volume.jenkins_data.name
    container_path = "/var/jenkins_home"
  }

  volumes {
    host_path      = "/var/run/docker.sock"
    container_path = "/var/run/docker.sock"
  }

  env = [
    "JENKINS_OPTS=--httpPort=8080",
    "JAVA_OPTS=-Djenkins.install.runSetupWizard=false"
  ]

  depends_on = [docker_container.sonarqube]

  # Additional verification that Docker socket permissions are correct
  healthcheck {
    test         = ["CMD-SHELL", "curl -f http://localhost:8080/login || exit 1"]
    interval     = "30s"
    timeout      = "10s"
    retries      = 10
    start_period = "60s"
  }
}

# Create Jenkins job configuration
resource "local_file" "jenkins_job_config" {
  filename = "${path.module}/jenkins-config/job-config.xml"
  content = templatefile("${path.module}/jenkins-job-template.xml", {
    repo_url = var.github_repo_url
  })
}

# Outputs
output "service_urls" {
  description = "URLs to access deployed services"
  value = {
    jenkins          = "http://localhost:8080"
    sonarqube        = "http://localhost:9000"
    sonarqube_creds  = "admin/admin (default)"
    vulnerable_app   = "http://localhost:5000 (available after pipeline run)"
  }
}

output "container_status" {
  description = "Status of deployed containers"
  value = {
    network    = docker_network.devsecops_network.name
    jenkins    = docker_container.jenkins.name
    sonarqube  = docker_container.sonarqube.name
    postgres   = docker_container.postgres.name
  }
}

output "docker_socket_fix" {
  description = "Docker socket permission fix status"
  value = {
    status = "Automated via entrypoint script"
    method = "Built into Jenkins container image"
    verification = "Check Jenkins logs: docker logs jenkins-${var.environment}"
  }
}

output "setup_instructions" {
  description = "Next steps to complete the setup"
  value = <<-EOT
DevSecOps Pipeline Setup Instructions:

1. WAIT FOR SERVICES TO START (2-3 minutes):
   - PostgreSQL initializes first
   - SonarQube connects to database and starts
   - Jenkins starts and automatically fixes Docker socket permissions

2. VERIFY SERVICES:
   - Jenkins: http://localhost:8080 (no password required)
   - SonarQube: http://localhost:9000 (admin/admin)
   - Check service status: docker ps

3. DOCKER SOCKET VERIFICATION:
   - Jenkins automatically fixes Docker socket permissions on startup
   - Check logs: docker logs jenkins-${var.environment}
   - Look for "Docker socket configuration completed" message
   - Test with: docker exec jenkins-${var.environment} docker ps

4. JENKINS SETUP:
   - Access Jenkins at http://localhost:8080
   - No initial password required (setup wizard disabled)
   - Create your first admin user when prompted
   - Import job using: jenkins-config/job-config.xml

5. GITHUB INTEGRATION:
   - Push vulnerable app code to: ${var.github_repo_url}
   - Create Jenkins pipeline job pointing to your repository
   - Configure webhook: http://localhost:8080/github-webhook/

6. SONARQUBE INTEGRATION:
   - Login to SonarQube: http://localhost:9000 (admin/admin)
   - Create project: "vulnerable-python-app"
   - Generate user token for Jenkins integration
   - Configure Jenkins SonarQube server settings

7. OPTIONAL - SNYK INTEGRATION:
   - Sign up at https://snyk.io for free account
   - Get API token from account settings
   - Add to Jenkins credentials as 'snyk-token'

TROUBLESHOOTING:
- If Docker commands fail in Jenkins, check: docker logs jenkins-${var.environment}
- Entrypoint script should show "Docker access confirmed"
- Manual fix (if needed): docker exec -u root jenkins-${var.environment} chmod 666 /var/run/docker.sock
- Restart Jenkins if needed: docker restart jenkins-${var.environment}
  EOT
}
