#!/bin/bash
set -e

echo "🔍 TGSession 部署验证脚本"
echo "=============================="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 函数定义
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查依赖
check_dependencies() {
    echo "📋 检查依赖..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装"
        exit 1
    fi
    log_info "Docker: $(docker --version)"
    
    if ! command -v docker-compose &> /dev/null; then
        log_warn "docker-compose 未安装，尝试使用 docker compose"
        if ! docker compose version &> /dev/null; then
            log_error "Docker Compose 不可用"
            exit 1
        fi
        DOCKER_COMPOSE="docker compose"
    else
        DOCKER_COMPOSE="docker-compose"
        log_info "Docker Compose: $(docker-compose --version)"
    fi
}

# 验证项目结构
validate_structure() {
    echo "📁 验证项目结构..."
    
    required_files=(
        "Dockerfile"
        "docker-compose.yml"
        "start.sh"
        "TGSession/api.py"
        "TGSession/requirements.txt"
        "TGSessionWeb/package.json"
        "TGSessionWeb/src/main.ts"
    )
    
    for file in "${required_files[@]}"; do
        if [[ -f "$file" ]]; then
            log_info "✓ $file"
        else
            log_error "✗ $file 缺失"
            exit 1
        fi
    done
}

# 构建测试
test_build() {
    echo "🔨 测试 Docker 构建..."
    
    # 构建镜像
    if docker build -t tgsession-test .; then
        log_info "Docker 构建成功"
    else
        log_error "Docker 构建失败"
        exit 1
    fi
    
    # 检查镜像
    if docker images | grep -q tgsession-test; then
        log_info "镜像创建成功"
    else
        log_error "镜像未找到"
        exit 1
    fi
}

# 运行测试
test_run() {
    echo "🚀 测试容器运行..."
    
    # 启动容器
    container_id=$(docker run -d -p 8080:80 --name tgsession-test-run tgsession-test)
    log_info "容器已启动: $container_id"
    
    # 等待服务启动
    echo "⏳ 等待服务启动..."
    sleep 10
    
    # 健康检查
    max_attempts=30
    attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f http://localhost:8080/health &> /dev/null; then
            log_info "健康检查通过"
            break
        fi
        
        if [ $attempt -eq $max_attempts ]; then
            log_error "健康检查失败"
            docker logs tgsession-test-run
            cleanup
            exit 1
        fi
        
        echo "尝试 $attempt/$max_attempts..."
        sleep 2
        ((attempt++))
    done
    
    # 测试前端
    if curl -f http://localhost:8080/ &> /dev/null; then
        log_info "前端访问正常"
    else
        log_warn "前端访问异常"
    fi
}

# Docker Compose 测试
test_compose() {
    echo "📦 测试 Docker Compose..."
    
    # 启动服务
    if $DOCKER_COMPOSE up -d; then
        log_info "Docker Compose 启动成功"
    else
        log_error "Docker Compose 启动失败"
        exit 1
    fi
    
    # 等待服务启动
    sleep 15
    
    # 检查服务状态
    if $DOCKER_COMPOSE ps | grep -q "Up"; then
        log_info "服务运行正常"
    else
        log_error "服务状态异常"
        $DOCKER_COMPOSE logs
        $DOCKER_COMPOSE down
        exit 1
    fi
    
    # 健康检查
    if curl -f http://localhost/health &> /dev/null; then
        log_info "Compose 健康检查通过"
    else
        log_error "Compose 健康检查失败"
        $DOCKER_COMPOSE logs
        $DOCKER_COMPOSE down
        exit 1
    fi
    
    # 停止服务
    $DOCKER_COMPOSE down
    log_info "Docker Compose 测试完成"
}

# 清理函数
cleanup() {
    echo "🧹 清理测试资源..."
    
    # 停止并删除容器
    if docker ps -a | grep -q tgsession-test-run; then
        docker stop tgsession-test-run &> /dev/null
        docker rm tgsession-test-run &> /dev/null
        log_info "测试容器已清理"
    fi
    
    # 删除测试镜像
    if docker images | grep -q tgsession-test; then
        docker rmi tgsession-test &> /dev/null
        log_info "测试镜像已清理"
    fi
    
    # 清理 Docker Compose
    if $DOCKER_COMPOSE ps &> /dev/null; then
        $DOCKER_COMPOSE down &> /dev/null
    fi
}

# 主函数
main() {
    # 捕获退出信号，确保清理
    trap cleanup EXIT
    
    check_dependencies
    validate_structure
    test_build
    test_run
    cleanup
    test_compose
    
    echo ""
    echo "🎉 所有测试通过！"
    echo "✅ Docker 镜像构建正常"
    echo "✅ 容器运行正常"
    echo "✅ 健康检查通过"
    echo "✅ Docker Compose 配置正确"
    echo ""
    echo "📝 接下来您可以："
    echo "   1. 推送代码到 GitHub 触发自动构建"
    echo "   2. 使用 docker-compose up -d 部署到生产环境"
    echo "   3. 配置域名和 SSL 证书"
}

# 如果直接运行脚本
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
