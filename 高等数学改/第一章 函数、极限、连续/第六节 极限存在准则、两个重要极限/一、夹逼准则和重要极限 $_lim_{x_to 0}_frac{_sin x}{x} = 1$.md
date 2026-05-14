### 一、夹逼准则和重要极限 $\lim_{x\to 0}\frac{\sin x}{x} = 1$

定理1.6.1 设（1）存在 $\eta > 0$ ，使得当 $0 < |x - x_0| < \eta$ 时，有

$$
g (x) \leqslant f (x) \leqslant h (x);
$$

(2) $\lim_{x \to x_0} g(x) = A$ 且 $\lim_{x \to x_0} h(x) = A$ ,

则当 $x \to x_0$ 时函数 $f(x)$ 的极限存在，且有

$$
\lim  _ {x \rightarrow x _ {0}} f (x) = A.
$$

证任意给定 $\varepsilon >0$ ，由 $\lim_{x\to x_0}g(x) = A,\lim_{x\to x_0}h(x) = A$ 可知，必存在正数 $\delta_1,\delta_2$ ，当 $0 <   |x - x_0| <   \delta_1$ 时，有 $|g(x) - A| <   \varepsilon$ ，即

$$
A - \varepsilon <   g (x) <   A + \varepsilon ;
$$

当 $0 < |x - x_0| < \delta_2$ 时，有 $|h(x) - A| < \varepsilon$ ，即

$$
A - \varepsilon <   h (x) <   A + \varepsilon .
$$

取 $\delta = \min \{\delta_1,\delta_2,\eta \}$ ，则当 $0 < |x - x_0| < \delta$ 时，不等式

$$
A - \varepsilon <   g (x) <   A + \varepsilon , A - \varepsilon <   h (x) <   A + \varepsilon
$$

及 $g(x)\leqslant f(x)\leqslant h(x)$ 同时成立.于是当 $0 <   |x - x_0| <   \delta$ 时，有

$$
A - \varepsilon <   g (x) \leqslant f (x) \leqslant h (x) <   A + \varepsilon ,
$$

即

$$
\left| f (x) - A \right| <   \varepsilon .
$$

根据极限的定义知 $\lim_{x\to x_0}f(x) = A$ （见图1.6.1）.

![](images/fc3feeca7a10c3874cf3ccc4fb5c9f074478abffcfb52343217e331520524c08.jpg)  
图1.6.1

对于函数极限的其他极限过程，亦有类似的定理.下面给出夹逼准则的数列形式

定理1.6.2 对于数列 $\{x_{n}\} \{y_{n}\} \{z_{n}\}$ ，设

（1）存在 $N_0\in \mathbb{N}_+$ ，当 $n > N_0$ 时，有 $y_{n}\leqslant x_{n}\leqslant z_{n}$   
(2) $\lim_{n\to \infty}y_n = a$ 且 $\lim_{n\to \infty}z_n = a$

则数列 $x_{n}$ 的极限存在，且有 $\lim_{n\to \infty}x_n = a$

夹逼准则不仅可以用来判断极限的存在，有时还可以用来求某些具体的极限.

例1.6.1 证明： $\lim_{n\to \infty}\left(\frac{1}{\sqrt{n^2 + 1}} +\frac{1}{\sqrt{n^2 + 2}} +\dots +\frac{1}{\sqrt{n^2 + n}}\right) = 1.$

证 令 $x_{n} = \frac{1}{\sqrt{n^{2} + 1}} + \frac{1}{\sqrt{n^{2} + 2}} + \dots + \frac{1}{\sqrt{n^{2} + n}}$ 可以看出 $x_{n}$ 是 $n$ 项之和， $n$ 项中最大的一项是 $\frac{1}{\sqrt{n^{2} + 1}}$ ，最小的一项是 $\frac{1}{\sqrt{n^{2} + n}}$ ，于是

$$
\frac {n}{\sqrt {n ^ {2} + n}} <   x _ {n} <   \frac {n}{\sqrt {n ^ {2} + 1}}.
$$

又因为

$$
\lim  _ {n \rightarrow \infty} \frac {n}{\sqrt {n ^ {2} + n}} = \lim  _ {n \rightarrow \infty} \frac {1}{\sqrt {1 + \frac {1}{n}}} = 1,
$$

$$
\lim  _ {n \rightarrow \infty} \frac {n}{\sqrt {n ^ {2} + 1}} = \lim  _ {n \rightarrow \infty} \frac {1}{\sqrt {1 + \frac {1}{n ^ {2}}}} = 1,
$$

所以由夹逼准则知极限 $\lim_{n\to \infty}x_n$ 存在，而且 $\lim_{n\to \infty}x_n = 1$

例1.6.2 设 $a > 0, b > 0$ ，证明 $\lim_{n\to \infty}\sqrt[n]{a^n + b^n} = \max \{a,b\}$

证 令 $E = \max \{a, b\}$ ，则

$$
\sqrt [ n ]{E ^ {n}} <   \sqrt [ n ]{a ^ {n} + b ^ {n}} \leqslant \sqrt [ n ]{E ^ {n} + E ^ {n}} = E \sqrt [ n ]{2}.
$$

而

$$
\lim  _ {n \rightarrow \infty} ^ {n} \sqrt {E ^ {n}} = \lim  _ {n \rightarrow \infty} E = E, \quad \lim  _ {n \rightarrow \infty} E ^ {n} \sqrt {2} = E \lim  _ {n \rightarrow \infty} ^ {n} \sqrt {2} = E,
$$

由夹逼准则知

$$
\lim  _ {n \rightarrow \infty} \sqrt [ n ]{a ^ {n} + b ^ {n}} = E = \max  \{a, b \}.
$$

下面利用夹逼准则证明重要极限

$$
\lim  _ {x \rightarrow 0} \frac {\sin x}{x} = 1. \tag {1.6.1}
$$

例1.6.3 证明： $\lim_{x\to 0}\frac{\sin x}{x} = 1.$

证 函数 $\frac{\sin x}{x}$ 除点 $x = 0$ 外，处处有定义. 首先假定 $0 < x < \frac{\pi}{2}$ .

作单位圆（见图1.6.2），设圆心角 $\angle AOB = x$ （弧度）．点 $B$ 处的切线与 $OA$ 的延长线交于 $D$ ， $AC\bot OB$ ，则

$\triangle AOB$ 的面积 $<$ 扇形 $AOB$ 的面积 $< \triangle DOB$ 的面积，所以

$$
\frac {1}{2} \sin x <   \frac {1}{2} x <   \frac {1}{2} \tan x,
$$

即

$$
\frac {1}{\sin x} > \frac {1}{x} > \frac {\cos x}{\sin x}, \tag {1.6.2}
$$

![](images/0e734347d200eb0069631d09ac80a00be395d9c1b3bb7e05bc6144b5007a33f6.jpg)  
图1.6.2

以 $\sin x$ 去乘式（1.6.2）得

$$
1 > \frac {\sin x}{x} > \cos x,
$$

由于 $\lim_{x\to 0^{+}}\cos x = 1,\lim_{x\to 0^{+}}1 = 1$ ，根据夹逼准则得

$$
\lim  _ {x \rightarrow 0 ^ {+}} \frac {\sin x}{x} = 1.
$$

其次假设 $-\frac{\pi}{2} < x < 0$ ，由于 $\frac{\sin x}{x}$ 是偶函数，故

$$
\lim  _ {x \rightarrow 0 ^ {-}} \frac {\sin x}{x} = \lim  _ {x \rightarrow 0 ^ {-}} \frac {\sin (- x)}{- x},
$$

令 $t = -x$ ，则当 $x\to 0^{-}$ 时， $t\to 0^{+}$ ，从而

$$
\lim  _ {x \to 0 ^ {-}} \frac {\sin x}{x} = \lim  _ {x \to 0 ^ {-}} \frac {\sin (- x)}{- x} = \lim  _ {t \to 0 ^ {+}} \frac {\sin t}{t} = 1.
$$

综上所述， $\lim_{x\to 0}\frac{\sin x}{x} = 1.$

极限（1.6.1）是一个很重要的极限，应用它可求出一些“ $\frac{0}{0}$ ”型未定式的极限。

例1.6.4 求 $\lim_{x\to 0}\frac{\tan x}{x}$

解 $\lim_{x\to 0}\frac{\tan x}{x} = \lim_{x\to 0}\left(\frac{\sin x}{\cos x}\cdot \frac{1}{x}\right) = \lim_{x\to 0}\frac{\sin x}{x}\cdot \lim_{x\to 0}\frac{1}{\cos x} = 1.$

例1.6.5 求 $\lim_{x\to 0}\frac{1 - \cos{x}}{x^2}.$

解 $\lim_{x\to 0}\frac{1 - \cos x}{x^2} = \lim_{x\to 0}\frac{2\sin^2\frac{x}{2}}{x^2} = \lim_{x\to 0}\frac{1}{2}\left(\frac{\sin\frac{x}{2}}{\frac{x}{2}}\right)^2 = \frac{1}{2}.$

例1.6.6 求 $\lim_{x\to 0}\frac{\sin 2x}{\sin 3x}.$

解 $\lim_{x\to 0}\frac{\sin 2x}{\sin 3x} = \lim_{x\to 0}\left(\frac{\sin 2x}{2x}\cdot \frac{2x}{3x}\cdot \frac{3x}{\sin 3x}\right)$

$$
= \frac {2}{3} \lim  _ {x \rightarrow 0} \frac {\sin 2 x}{2 x} \cdot \lim  _ {x \rightarrow 0} \frac {3 x}{\sin 3 x} = \frac {2}{3}.
$$

例1.6.7 求 $\lim_{x\to \pi}\frac{\sin x}{x - \pi}.$

解 令 $t = \pi - x$ ，则 $x \to \pi$ 时 $t \to 0$ ，于是

$$
\lim  _ {x \rightarrow \pi} \frac {\sin x}{x - \pi} = \lim  _ {x \rightarrow \pi} \frac {\sin (\pi - x)}{x - \pi} = \lim  _ {t \rightarrow 0} \frac {\sin t}{- t} = - 1.
$$

