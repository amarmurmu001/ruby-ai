import numpy as np

class Dense:
    def __init__(self, n_inputs: int, n_neurons: int):
        self.weights = np.random.randn(n_inputs, n_neurons) * np.sqrt(2.0 / n_inputs)
        self.biases = np.zeros((1, n_neurons))
        self.input = None
        self.output = None
        self.dweights = None
        self.dbiases = None

    def forward(self, inputs: np.ndarray) -> np.ndarray:
        self.input = inputs
        self.output = np.dot(inputs, self.weights) + self.biases
        return self.output

    def backward(self, dvalues: np.ndarray) -> np.ndarray:
        self.dweights = np.dot(self.input.T, dvalues)
        self.dbiases = np.sum(dvalues, axis=0, keepdims=True)
        return np.dot(dvalues, self.weights.T)

    def update(self, lr: float = 0.01):
        self.weights -= lr * self.dweights
        self.biases -= lr * self.dbiases

class ReLU:
    def __init__(self):
        self.input = None
        self.output = None

    def forward(self, inputs: np.ndarray) -> np.ndarray:
        self.input = inputs
        self.output = np.maximum(0, inputs)
        return self.output

    def backward(self, dvalues: np.ndarray) -> np.ndarray:
        return dvalues * (self.input > 0)

class Softmax:
    def __init__(self):
        self.output = None

    def forward(self, inputs: np.ndarray) -> np.ndarray:
        exp = np.exp(inputs - np.max(inputs, axis=1, keepdims=True))
        self.output = exp / np.sum(exp, axis=1, keepdims=True)
        return self.output

    def backward(self, dvalues: np.ndarray) -> np.ndarray:
        return dvalues

class Tanh:
    def __init__(self):
        self.input = None
        self.output = None

    def forward(self, inputs: np.ndarray) -> np.ndarray:
        self.input = inputs
        self.output = np.tanh(inputs)
        return self.output

    def backward(self, dvalues: np.ndarray) -> np.ndarray:
        return dvalues * (1 - self.output ** 2)

class Sigmoid:
    def __init__(self):
        self.input = None
        self.output = None

    def forward(self, inputs: np.ndarray) -> np.ndarray:
        self.input = inputs
        self.output = 1 / (1 + np.exp(-np.clip(inputs, -500, 500)))
        return self.output

    def backward(self, dvalues: np.ndarray) -> np.ndarray:
        return dvalues * self.output * (1 - self.output)

def categorical_crossentropy(y_pred: np.ndarray, y_true: np.ndarray) -> float:
    return -np.mean(np.log(y_pred[range(len(y_pred)), y_true] + 1e-7))

def accuracy(y_pred: np.ndarray, y_true: np.ndarray) -> float:
    return np.mean(np.argmax(y_pred, axis=1) == y_true)
