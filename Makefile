# Makefile for FX Analysis System

.PHONY: help install test audit docker-build docker-run clean

# Default target
help:
	@echo "Available targets:"
	@echo "  install      - Install dependencies in virtual environment"
	@echo "  test         - Run smoke tests"
	@echo "  audit        - Run AWS configuration audit"
	@echo "  audit-json   - Run AWS audit and output JSON only"
	@echo "  docker-build - Build Docker image"
	@echo "  docker-run   - Run Docker container"
	@echo "  clean        - Clean up generated files"
	@echo "  run-local    - Run the application locally"

# Install dependencies
install:
	@echo "Installing dependencies..."
	@python3 -m venv venv
	@./venv/bin/pip install --upgrade pip
	@./venv/bin/pip install -r requirements.txt
	@./venv/bin/pip install tabulate  # Additional for audit script
	@echo "✅ Dependencies installed"

# Run smoke tests
test:
	@echo "Running smoke tests..."
	@./venv/bin/python scripts/smoke_test.py

# Run AWS configuration audit
audit:
	@echo "Running AWS configuration audit..."
	@if [ ! -d "venv" ]; then make install; fi
	@./venv/bin/pip install -q tabulate 2>/dev/null || true
	@./venv/bin/python scripts/audit_aws.py

# Run AWS audit with JSON output only
audit-json:
	@./venv/bin/python scripts/audit_aws.py 2>/dev/null | tail -n 1

# Build Docker image
docker-build:
	@echo "Building Docker image..."
	docker build -t analyze-fx:latest .
	@echo "✅ Docker image built: analyze-fx:latest"

# Run Docker container
docker-run:
	@echo "Running Docker container..."
	@if [ ! -f .env ]; then \
		echo "❌ .env file not found! Copy .env.example to .env and configure."; \
		exit 1; \
	fi
	docker-compose up

# Clean up generated files
clean:
	@echo "Cleaning up..."
	@rm -rf venv/
	@rm -rf __pycache__/
	@rm -rf src/__pycache__/
	@rm -rf src/*/__pycache__/
	@rm -f audit_report.json
	@rm -rf logs/
	@find . -name "*.pyc" -delete
	@find . -name ".pytest_cache" -type d -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Cleaned up"

# Run application locally
run-local:
	@echo "Running application locally..."
	@if [ ! -f .env ]; then \
		echo "❌ .env file not found! Copy .env.example to .env and configure."; \
		exit 1; \
	fi
	@if [ ! -d "venv" ]; then make install; fi
	@./venv/bin/python -m src.runner.main

# AWS setup and deployment helpers
.PHONY: setup setup-dry-run ecr-login ecr-push deploy

# Setup AWS environment
setup:
	@echo "Setting up AWS environment..."
	@if [ ! -d "venv" ]; then make install; fi
	@./venv/bin/python scripts/setup_aws.py

# Dry run setup (no resources created)
setup-dry-run:
	@echo "Running setup in dry-run mode..."
	@if [ ! -d "venv" ]; then make install; fi
	@./venv/bin/python scripts/setup_aws.py --dry-run

# Login to ECR
ecr-login:
	@echo "Logging in to ECR..."
	aws ecr get-login-password --region ap-northeast-1 | \
		docker login --username AWS --password-stdin 455931011903.dkr.ecr.ap-northeast-1.amazonaws.com

# Push to ECR
ecr-push: docker-build ecr-login
	@echo "Pushing to ECR..."
	docker tag analyze-fx:latest 455931011903.dkr.ecr.ap-northeast-1.amazonaws.com/analyze-fx:latest
	docker push 455931011903.dkr.ecr.ap-northeast-1.amazonaws.com/analyze-fx:latest
	@echo "✅ Pushed to ECR"

# Deploy to ECS (update service)
deploy: ecr-push
	@echo "Updating ECS service..."
	aws ecs update-service \
		--cluster analyze-fx-cluster \
		--service analyze-fx-service \
		--force-new-deployment \
		--region ap-northeast-1
	@echo "✅ Deployment initiated"