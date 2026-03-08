from typing import Dict, Any, Type, Callable, Optional

class ServiceContainer:
    """简单的依赖注入容器"""
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, Callable] = {}
    
    def register(self, name: str, instance: Any) -> None:
        """注册服务实例"""
        self._services[name] = instance
    
    def register_factory(self, name: str, factory: Callable) -> None:
        """注册服务工厂"""
        self._factories[name] = factory
    
    def get(self, name: str) -> Any:
        """获取服务实例"""
        if name in self._services:
            return self._services[name]
        if name in self._factories:
            instance = self._factories[name](self)
            self._services[name] = instance
            return instance
        raise KeyError(f"Service '{name}' not registered")
    
    def has(self, name: str) -> bool:
        """检查服务是否已注册"""
        return name in self._services or name in self._factories
