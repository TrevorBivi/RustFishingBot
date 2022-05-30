import numpy as np
from scipy.fft import fft, ifft
from scipy.fft import fft, fftfreq

from nfft import nfft, ndft
import matplotlib.pyplot as plt

# define evaluation points
x = -0.5 + np.random.rand(50)

# define Fourier coefficients
N = 2
k = - N // 2 + np.arange(N)
f_k = np.random.randn(N)
print(f_k[:80])
# non-equispaced fast Fourier transform
f = ndft(x, f_k)


plt.plot(np.fft.fftfreq(len(x)), abs(f))
plt.show()
