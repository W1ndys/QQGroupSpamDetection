document.addEventListener('DOMContentLoaded', () => {
    // 获取Canvas和Context
    const canvas = document.getElementById('starfield');
    const ctx = canvas.getContext('2d');

    // 设置Canvas尺寸为窗口大小
    function resizeCanvas() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    }
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    // 鼠标位置追踪
    let mouseX = 0;
    let mouseY = 0;
    let targetX = 0;
    let targetY = 0;

    // 速度控制
    let speedFactor = 1;
    const maxSpeed = 5;
    const minSpeed = 0.1;
    
    // 星星参数
    const starCount = 1500;
    const stars = [];
    const maxZ = 1000;
    const minZ = 1;
    
    // 视野和透视参数
    const fov = 250; // 视野范围
    let cameraX = 0;
    let cameraY = 0;

    // 星星类
    class Star {
        constructor() {
            this.reset();
        }
        
        reset() {
            // 随机3D坐标
            this.x = (Math.random() * 2 - 1) * canvas.width * 2;
            this.y = (Math.random() * 2 - 1) * canvas.height * 2;
            this.z = Math.random() * maxZ + minZ;
            
            // 星星基本属性
            this.size = Math.random() * 1.5 + 0.5;
            this.baseColor = Math.floor(Math.random() * 360);
            this.tailPoints = [];
            this.maxTailLength = Math.floor(Math.random() * 10) + 5;
        }
        
        // 更新星星位置
        update() {
            // Z轴移动，实现穿梭效果
            this.z -= speedFactor * 5;
            
            // 如果星星移出视野范围，重置它
            if (this.z < minZ) {
                this.reset();
                this.z = maxZ;
            }
            
            // 保存拖尾点
            if (speedFactor > 2) {
                if (this.tailPoints.length > this.maxTailLength) {
                    this.tailPoints.shift();
                }
                this.tailPoints.push({
                    x: this.projectX(),
                    y: this.projectY(),
                });
            } else {
                this.tailPoints = [];
            }
        }
        
        // X轴透视投影
        projectX() {
            const perspective = fov / (this.z + fov);
            return (this.x - cameraX) * perspective + canvas.width / 2;
        }
        
        // Y轴透视投影
        projectY() {
            const perspective = fov / (this.z + fov);
            return (this.y - cameraY) * perspective + canvas.height / 2;
        }
        
        // 绘制星星
        draw() {
            // 透视投影
            const x = this.projectX();
            const y = this.projectY();
            
            // 根据Z轴计算亮度和大小
            const brightness = Math.min(1, (maxZ - this.z) / maxZ);
            const alpha = brightness * 0.8 + 0.2;
            const scale = this.size * (1 - this.z / maxZ) * 2;
            
            // 绘制拖尾
            if (this.tailPoints.length > 1 && speedFactor > 2) {
                ctx.beginPath();
                ctx.moveTo(x, y);
                
                for (let i = this.tailPoints.length - 1; i >= 0; i--) {
                    const point = this.tailPoints[i];
                    ctx.lineTo(point.x, point.y);
                    
                    // 绘制拖尾点
                    const pointAlpha = alpha * (i / this.tailPoints.length) * 0.5;
                    ctx.fillStyle = `hsla(${this.baseColor}, 100%, 80%, ${pointAlpha})`;
                    ctx.fillRect(point.x, point.y, scale * 0.8, scale * 0.8);
                }
                
                // 设置渐变拖尾
                ctx.strokeStyle = `hsla(${this.baseColor}, 100%, 70%, ${alpha * 0.3})`;
                ctx.lineWidth = scale * 0.5;
                ctx.stroke();
            }
            
            // 绘制星星主体
            ctx.beginPath();
            ctx.arc(x, y, scale, 0, Math.PI * 2);
            
            // 设置发光效果
            const glow = ctx.createRadialGradient(x, y, 0, x, y, scale * 2);
            glow.addColorStop(0, `hsla(${this.baseColor}, 100%, 80%, ${alpha})`);
            glow.addColorStop(0.4, `hsla(${this.baseColor}, 100%, 70%, ${alpha * 0.6})`);
            glow.addColorStop(1, `hsla(${this.baseColor}, 100%, 60%, 0)`);
            
            ctx.fillStyle = glow;
            ctx.fill();
            
            // 中心亮点
            ctx.fillStyle = `rgba(255, 255, 255, ${alpha})`;
            ctx.beginPath();
            ctx.arc(x, y, scale * 0.5, 0, Math.PI * 2);
            ctx.fill();
        }
    }

    // 初始化星星
    function initStars() {
        for (let i = 0; i < starCount; i++) {
            stars.push(new Star());
        }
    }

    // 更新场景
    function update() {
        // 平滑相机移动
        cameraX += (targetX - cameraX) * 0.02;
        cameraY += (targetY - cameraY) * 0.02;
        
        // 更新每个星星
        stars.forEach(star => star.update());
    }

    // 渲染场景
    function render() {
        // 清除画布
        ctx.fillStyle = 'rgba(0, 0, 0, 0.2)';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        
        // 绘制每个星星
        stars.forEach(star => star.draw());
        
        // 添加轻微的径向渐变背景，增强深度感
        const centerX = canvas.width / 2;
        const centerY = canvas.height / 2;
        const radius = Math.max(canvas.width, canvas.height);
        
        const gradient = ctx.createRadialGradient(centerX, centerY, 0, centerX, centerY, radius);
        gradient.addColorStop(0, 'rgba(15, 30, 60, 0.1)');
        gradient.addColorStop(1, 'rgba(0, 0, 0, 0)');
        
        ctx.fillStyle = gradient;
        ctx.fillRect(0, 0, canvas.width, canvas.height);
    }

    // 动画循环
    function animate() {
        update();
        render();
        requestAnimationFrame(animate);
    }

    // 事件监听器
    function setupEventListeners() {
        // 鼠标移动
        document.addEventListener('mousemove', (e) => {
            mouseX = e.clientX;
            mouseY = e.clientY;
            
            // 转换鼠标位置为相机目标位置
            targetX = (mouseX - canvas.width / 2) * 2;
            targetY = (mouseY - canvas.height / 2) * 2;
        });
        
        // 触摸移动
        document.addEventListener('touchmove', (e) => {
            e.preventDefault();
            mouseX = e.touches[0].clientX;
            mouseY = e.touches[0].clientY;
            
            targetX = (mouseX - canvas.width / 2) * 2;
            targetY = (mouseY - canvas.height / 2) * 2;
        });
        
        // 鼠标滚轮控制速度
        document.addEventListener('wheel', (e) => {
            e.preventDefault();
            
            speedFactor += e.deltaY * 0.001;
            
            // 限制速度范围
            speedFactor = Math.max(minSpeed, Math.min(maxSpeed, speedFactor));
        }, { passive: false });
    }

    // 初始化并启动动画
    initStars();
    setupEventListeners();
    animate();
}); 