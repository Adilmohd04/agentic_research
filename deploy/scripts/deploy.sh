#!/bin/bash

# Agentic Research Copilot Deployment Script
# This script handles deployment to various environments

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
DOCKER_REGISTRY="${DOCKER_REGISTRY:-localhost:5000}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
ENVIRONMENT="${ENVIRONMENT:-development}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Help function
show_help() {
    cat << EOF
Agentic Research Copilot Deployment Script

Usage: $0 [OPTIONS] COMMAND

Commands:
    build       Build Docker images
    deploy      Deploy to specified environment
    test        Run deployment tests
    rollback    Rollback to previous version
    status      Check deployment status
    logs        View application logs
    cleanup     Clean up resources

Options:
    -e, --environment ENV    Target environment (development|staging|production)
    -t, --tag TAG           Docker image tag (default: latest)
    -r, --registry URL      Docker registry URL
    -h, --help              Show this help message

Examples:
    $0 build
    $0 deploy -e production -t v1.2.3
    $0 status -e staging
    $0 logs -e production

EOF
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    local missing_tools=()
    
    # Check for required tools
    command -v docker >/dev/null 2>&1 || missing_tools+=("docker")
    command -v docker-compose >/dev/null 2>&1 || missing_tools+=("docker-compose")
    
    if [[ "$ENVIRONMENT" == "production" ]]; then
        command -v kubectl >/dev/null 2>&1 || missing_tools+=("kubectl")
        command -v helm >/dev/null 2>&1 || missing_tools+=("helm")
    fi
    
    if [[ ${#missing_tools[@]} -gt 0 ]]; then
        log_error "Missing required tools: ${missing_tools[*]}"
        log_error "Please install the missing tools and try again."
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Build Docker images
build_images() {
    log_info "Building Docker images..."
    
    cd "$PROJECT_ROOT"
    
    # Build backend image
    log_info "Building backend image..."
    docker build -t "${DOCKER_REGISTRY}/agentic-research-backend:${IMAGE_TAG}" \
        --target backend \
        --build-arg BUILD_DATE="$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
        --build-arg VCS_REF="$(git rev-parse --short HEAD)" \
        .
    
    # Build frontend image
    log_info "Building frontend image..."
    docker build -t "${DOCKER_REGISTRY}/agentic-research-frontend:${IMAGE_TAG}" \
        --target frontend \
        --build-arg BUILD_DATE="$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
        --build-arg VCS_REF="$(git rev-parse --short HEAD)" \
        .
    
    log_success "Docker images built successfully"
}

# Push images to registry
push_images() {
    if [[ "$DOCKER_REGISTRY" != "localhost:5000" ]]; then
        log_info "Pushing images to registry..."
        
        docker push "${DOCKER_REGISTRY}/agentic-research-backend:${IMAGE_TAG}"
        docker push "${DOCKER_REGISTRY}/agentic-research-frontend:${IMAGE_TAG}"
        
        log_success "Images pushed to registry"
    fi
}

# Deploy to development environment
deploy_development() {
    log_info "Deploying to development environment..."
    
    cd "$PROJECT_ROOT"
    
    # Create necessary directories
    mkdir -p logs data docker/ssl
    
    # Generate self-signed SSL certificate for development
    if [[ ! -f docker/ssl/cert.pem ]]; then
        log_info "Generating self-signed SSL certificate..."
        openssl req -x509 -newkey rsa:4096 -keyout docker/ssl/key.pem -out docker/ssl/cert.pem \
            -days 365 -nodes -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
    fi
    
    # Start services
    docker-compose up -d
    
    # Wait for services to be ready
    log_info "Waiting for services to be ready..."
    sleep 30
    
    # Run health checks
    check_health_development
    
    log_success "Development deployment completed"
}

# Deploy to production environment
deploy_production() {
    log_info "Deploying to production environment..."
    
    # Check if kubectl is configured
    if ! kubectl cluster-info >/dev/null 2>&1; then
        log_error "kubectl is not configured or cluster is not accessible"
        exit 1
    fi
    
    cd "$PROJECT_ROOT"
    
    # Apply Kubernetes manifests
    log_info "Applying Kubernetes manifests..."
    kubectl apply -f deploy/kubernetes/namespace.yaml
    kubectl apply -f deploy/kubernetes/secrets.yaml
    kubectl apply -f deploy/kubernetes/configmap.yaml
    kubectl apply -f deploy/kubernetes/pvc.yaml
    kubectl apply -f deploy/kubernetes/backend-deployment.yaml
    kubectl apply -f deploy/kubernetes/frontend-deployment.yaml
    kubectl apply -f deploy/kubernetes/ingress.yaml
    
    # Wait for rollout to complete
    log_info "Waiting for deployment rollout..."
    kubectl rollout status deployment/agentic-research-backend -n agentic-research --timeout=300s
    kubectl rollout status deployment/agentic-research-frontend -n agentic-research --timeout=300s
    
    # Run health checks
    check_health_production
    
    log_success "Production deployment completed"
}

# Health checks for development
check_health_development() {
    log_info "Running health checks..."
    
    local max_attempts=30
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        if curl -f http://localhost:8000/health >/dev/null 2>&1; then
            log_success "Backend health check passed"
            break
        fi
        
        if [[ $attempt -eq $max_attempts ]]; then
            log_error "Backend health check failed after $max_attempts attempts"
            return 1
        fi
        
        log_info "Attempt $attempt/$max_attempts: Backend not ready, waiting..."
        sleep 10
        ((attempt++))
    done
    
    # Check frontend
    if curl -f http://localhost/ >/dev/null 2>&1; then
        log_success "Frontend health check passed"
    else
        log_warning "Frontend health check failed"
    fi
}

# Health checks for production
check_health_production() {
    log_info "Running production health checks..."
    
    # Check pod status
    kubectl get pods -n agentic-research
    
    # Check service endpoints
    kubectl get endpoints -n agentic-research
    
    # Wait for pods to be ready
    kubectl wait --for=condition=ready pod -l app=agentic-research-backend -n agentic-research --timeout=300s
    kubectl wait --for=condition=ready pod -l app=agentic-research-frontend -n agentic-research --timeout=300s
    
    log_success "Production health checks passed"
}

# Run tests
run_tests() {
    log_info "Running deployment tests..."
    
    cd "$PROJECT_ROOT/backend"
    
    # Run test suite
    python run_tests.py --fast
    
    log_success "Tests completed"
}

# Check deployment status
check_status() {
    log_info "Checking deployment status for environment: $ENVIRONMENT"
    
    case $ENVIRONMENT in
        development)
            docker-compose ps
            ;;
        production)
            kubectl get all -n agentic-research
            kubectl top pods -n agentic-research 2>/dev/null || log_warning "Metrics server not available"
            ;;
        *)
            log_error "Unknown environment: $ENVIRONMENT"
            exit 1
            ;;
    esac
}

# View logs
view_logs() {
    log_info "Viewing logs for environment: $ENVIRONMENT"
    
    case $ENVIRONMENT in
        development)
            docker-compose logs -f --tail=100
            ;;
        production)
            kubectl logs -f -l app=agentic-research-backend -n agentic-research --tail=100
            ;;
        *)
            log_error "Unknown environment: $ENVIRONMENT"
            exit 1
            ;;
    esac
}

# Cleanup resources
cleanup() {
    log_info "Cleaning up resources for environment: $ENVIRONMENT"
    
    case $ENVIRONMENT in
        development)
            docker-compose down -v
            docker system prune -f
            ;;
        production)
            kubectl delete namespace agentic-research
            ;;
        *)
            log_error "Unknown environment: $ENVIRONMENT"
            exit 1
            ;;
    esac
    
    log_success "Cleanup completed"
}

# Rollback deployment
rollback() {
    log_info "Rolling back deployment for environment: $ENVIRONMENT"
    
    case $ENVIRONMENT in
        development)
            log_warning "Rollback not implemented for development environment"
            log_info "Use 'docker-compose down && docker-compose up -d' to restart"
            ;;
        production)
            kubectl rollout undo deployment/agentic-research-backend -n agentic-research
            kubectl rollout undo deployment/agentic-research-frontend -n agentic-research
            ;;
        *)
            log_error "Unknown environment: $ENVIRONMENT"
            exit 1
            ;;
    esac
    
    log_success "Rollback completed"
}

# Main function
main() {
    local command=""
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -e|--environment)
                ENVIRONMENT="$2"
                shift 2
                ;;
            -t|--tag)
                IMAGE_TAG="$2"
                shift 2
                ;;
            -r|--registry)
                DOCKER_REGISTRY="$2"
                shift 2
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            build|deploy|test|rollback|status|logs|cleanup)
                command="$1"
                shift
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # Validate environment
    case $ENVIRONMENT in
        development|staging|production)
            ;;
        *)
            log_error "Invalid environment: $ENVIRONMENT"
            log_error "Valid environments: development, staging, production"
            exit 1
            ;;
    esac
    
    # Execute command
    case $command in
        build)
            check_prerequisites
            build_images
            push_images
            ;;
        deploy)
            check_prerequisites
            build_images
            push_images
            case $ENVIRONMENT in
                development)
                    deploy_development
                    ;;
                production)
                    deploy_production
                    ;;
                *)
                    log_error "Deployment not implemented for environment: $ENVIRONMENT"
                    exit 1
                    ;;
            esac
            ;;
        test)
            run_tests
            ;;
        rollback)
            rollback
            ;;
        status)
            check_status
            ;;
        logs)
            view_logs
            ;;
        cleanup)
            cleanup
            ;;
        *)
            log_error "No command specified"
            show_help
            exit 1
            ;;
    esac
}

# Run main function
main "$@"