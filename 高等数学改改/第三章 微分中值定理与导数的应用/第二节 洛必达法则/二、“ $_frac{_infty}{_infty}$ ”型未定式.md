### 二、“ $\frac{\infty}{\infty}$ ”型未定式

“ $\frac{\infty}{\infty}$ ”型未定式的计算也有相应的洛必达法则，我们不加证明地直接给出.

定理3.2.2 设函数 $f(x), F(x)$ 在点 $a$ 的某个去心邻域 $\mathring{U}(a, \delta)$ 内有定义，而且满足以下条件：

(1) $\lim_{x\to a}f(x) = \infty ,\lim_{x\to a}F(x) = \infty ;$   
（2）在 $\mathring{U}(a, \delta)$ 内， $f'(x)$ 和 $F'(x)$ 均存在，且 $F'(x) \neq 0$ ；  
（3） $\lim_{x\to a}\frac{f'(x)}{F'(x)} = k$ （或 $\infty$ ），其中 $k$ 是常数，

则

$$
\lim  _ {x \to a} {\frac {f (x)}{F (x)}} = \lim  _ {x \to a} {\frac {f ^ {\prime} (x)}{F ^ {\prime} (x)}} = k \quad (\text {或} \infty) .
$$

推论3.2.2 设当 $|x| > X$ 时，函数 $f(x), F(x)$ 有定义，而且满足以下条件：

（1） $\lim_{x\to \infty}f(x) = \infty ,\lim_{x\to \infty}F(x) = \infty ;$   
（2）当 $|x| > X$ 时， $f'(x)$ 和 $F''(x)$ 均存在，且 $F'(x) \neq 0$ ；  
（3） $\lim_{x\to \infty}\frac{f'(x)}{F'(x)} = k$ （或 $\infty$ ），其中 $k$ 是常数，

则

$$
\lim  _ {x \to \infty} {\frac {f (x)}{F (x)}} = \lim  _ {x \to \infty} {\frac {f ^ {\prime} (x)}{F ^ {\prime} (x)}} = k \quad (\text {或} \infty) .
$$

当 $x \to a^{+}, x \to a^{-}, x \to +\infty, x \to -\infty$ 时，“ $\frac{\infty}{\infty}$ ”型未定式也有类似的洛必达法则.

例3.2.7 求 $\lim_{x\to 0^{+}}\frac{\ln(\sin x)}{\cot x}.$

解这是 $\frac{\infty}{\infty}$ 型未定式，由洛必达法则得

$$
\lim  _ {x \rightarrow 0 ^ {+}} \frac {\ln (\sin x)}{\cot x} = \lim  _ {x \rightarrow 0 ^ {+}} \frac {\frac {\cos x}{\sin x}}{- \frac {1}{\sin^ {2} x}} = - \frac {1}{2} \lim  _ {x \rightarrow 0 ^ {+}} \sin 2 x = 0.
$$

例3.2.8 求 $\lim_{x\to +\infty}\frac{\ln(2x^2 + x + 1)}{\ln(x^2 + 2x + 3)}.$

解这是 $\frac{\infty}{\infty}$ 型不定式，由洛必达法则得

$$
\lim  _ {x \rightarrow + \infty} \frac {\ln (2 x ^ {2} + x + 1)}{\ln (x ^ {2} + 2 x + 3)} = \lim  _ {x \rightarrow + \infty} \frac {\frac {4 x + 1}{2 x ^ {2} + x + 1}}{\frac {2 x + 2}{x ^ {2} + 2 x + 3}} = \lim  _ {x \rightarrow + \infty} \frac {(4 x + 1) (x ^ {2} + 2 x + 3)}{(2 x + 2) (2 x ^ {2} + x + 1)} = 1.
$$

例3.2.9 求 $\lim_{x\to +\infty}\frac{x^n}{\mathrm{e}^x}$ $(n\in \mathbb{N}_{+})$

解这是“ $\frac{\infty}{\infty}$ ”型未定式，连续应用洛必达法则 $n$ 次，得到

$$
\lim  _ {x \rightarrow + \infty} \frac {x ^ {n}}{\mathrm {e} ^ {x}} = \lim  _ {x \rightarrow + \infty} \frac {n x ^ {n - 1}}{\mathrm {e} ^ {x}} = \lim  _ {x \rightarrow + \infty} \frac {n (n - 1) x ^ {n - 2}}{\mathrm {e} ^ {x}} = \dots = \lim  _ {x \rightarrow + \infty} \frac {n !}{\mathrm {e} ^ {x}} = 0.
$$

例3.2.9说明，当 $x\to +\infty$ 时， $\mathrm{e}^x$ 的增长速度比 $x^n$ $(n\in \mathbb{N}_{+})$ 快.还可以证明

$$
\lim  _ {x \rightarrow + \infty} \frac {x ^ {\mu}}{\mathrm {e} ^ {x}} = 0 \quad (\mu > 0).
$$

例3.2.10 求 $\lim_{x\to +\infty}\frac{\ln x}{x^{\mu}} (\mu >0)$

解 $\lim_{x\to +\infty}\frac{\ln x}{x^{\mu}} = \lim_{x\to +\infty}\frac{\frac{1}{x}}{\mu x^{\mu - 1}} = \lim_{x\to +\infty}\frac{1}{\mu x^{\mu}} = 0.$

例3.2.10说明，当 $x\to +\infty$ 时， $x^{\mu}(\mu >0)$ 的增长速度比 $\ln x$ 快

