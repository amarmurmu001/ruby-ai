import numpy as np

class SGD:
    def __init__(self, lr: float = 0.01, momentum: float = 0.0):
        self.lr = lr
        self.momentum = momentum
        self.velocities = []

    def update_params(self, layer, layer_idx: int, velocities: list):
        if len(velocities) <= layer_idx:
            velocities.append({
                'w': np.zeros_like(layer.weights),
                'b': np.zeros_like(layer.biases)
            })
        v = velocities[layer_idx]
        v['w'] = self.momentum * v['w'] - self.lr * layer.dweights
        v['b'] = self.momentum * v['b'] - self.lr * layer.dbiases
        layer.weights += v['w']
        layer.biases += v['b']

class Adam:
    def __init__(self, lr: float = 0.001, beta1: float = 0.9, beta2: float = 0.999, eps: float = 1e-8):
        self.lr = lr
        self.beta1 = beta1
        self.beta2 = beta2
        self.eps = eps
        self.t = 0
        self.m = []
        self.v = []

    def update_params(self, layer, layer_idx: int, _velocities=None):
        if len(self.m) <= layer_idx:
            self.m.append({'w': np.zeros_like(layer.weights), 'b': np.zeros_like(layer.biases)})
            self.v.append({'w': np.zeros_like(layer.weights), 'b': np.zeros_like(layer.biases)})

        self.t += 1
        m = self.m[layer_idx]
        v = self.v[layer_idx]

        m['w'] = self.beta1 * m['w'] + (1 - self.beta1) * layer.dweights
        m['b'] = self.beta1 * m['b'] + (1 - self.beta1) * layer.dbiases
        v['w'] = self.beta2 * v['w'] + (1 - self.beta2) * (layer.dweights ** 2)
        v['b'] = self.beta2 * v['b'] + (1 - self.beta2) * (layer.dbiases ** 2)

        m_hat_w = m['w'] / (1 - self.beta1 ** self.t)
        m_hat_b = m['b'] / (1 - self.beta1 ** self.t)
        v_hat_w = v['w'] / (1 - self.beta2 ** self.t)
        v_hat_b = v['b'] / (1 - self.beta2 ** self.t)

        layer.weights -= self.lr * m_hat_w / (np.sqrt(v_hat_w) + self.eps)
        layer.biases -= self.lr * m_hat_b / (np.sqrt(v_hat_b) + self.eps)
