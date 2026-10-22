import csv, math
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.optimize import least_squares
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image,
    PageBreak, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

O=Path(__file__).resolve().parent
rng=np.random.default_rng(20261023)
N=100
records=[]
figures=[]

def g(x,c,s):
    return np.exp(-.5*((x-c)/s)**2)

def evaluate(name, unit, simulator):
    rows=[]
    example=None
    for i in range(N):
        try:
            truth,old,new,xx,yy,oldcurve,newcurve=simulator()
            if not all(np.isfinite([truth,old,new])):
                continue
            a=abs(old-truth)
            b=abs(new-truth)
            rows.append((a,b))
            records.append([name,i,truth,old,new,a,b])
            if example is None:
                example=(xx,yy,oldcurve,newcurve)
        except Exception:
            continue

    if len(rows)<80:
        raise RuntimeError(
            f"{name}: only {len(rows)}/{N} successful trials"
        )

    errors=np.array(rows)
    a,b=errors.T
    improvement=100*(a.mean()-b.mean())/a.mean()

    # Paired bootstrap of mean-error reduction
    ix=rng.integers(0,len(a),(3000,len(a)))
    av=a[ix].mean(axis=1)
    bv=b[ix].mean(axis=1)
    ci=np.percentile(100*(av-bv)/av,[2.5,97.5])

    fig,axs=plt.subplots(1,2,figsize=(11,4.3))
    x,y,oldfit,newfit=example
    axs[0].plot(x,y,'.',ms=2,color='#7899ad',
                label='Observed')
    axs[0].plot(x,oldfit,lw=1.6,color='#ba7553',
                label='Without')
    axs[0].plot(x,newfit,lw=1.6,color='#087d64',
                label='With')
    axs[0].set_title('Same observation')
    axs[0].set_xlabel('Measurement coordinate')
    axs[0].set_ylabel('Signal / estimator')
    axs[0].legend(fontsize=8)
    axs[1].boxplot([a,b],tick_labels=['Without','With'],
                   showfliers=False)
    axs[1].set_title(f'Absolute error · {len(a)} trials')
    axs[1].set_ylabel(unit)
    for ax in axs:
        ax.spines[['top','right']].set_visible(False)
        ax.grid(alpha=.12)
    fig.suptitle(name,fontsize=15,fontweight='bold')
    fig.tight_layout()
    fn=O/(name.split(':')[0].lower()+'_comparison.png')
    fig.savefig(fn,dpi=180,bbox_inches='tight')
    plt.close(fig)
    figures.append((name,fn,improvement,ci,len(a)))
    print(name, f'{improvement:+.1f}% [{ci[0]:+.1f}, {ci[1]:+.1f}]')

# 1. XRD: Cu doublet versus single-line centroid model.
# Target is a known Si lattice parameter.
def xrd():
    a=rng.uniform(5.38,5.48)
    lam1,lam2=1.54056,1.54439
    h2=11
    centre=lambda lam:2*np.degrees(
        np.arcsin(lam*np.sqrt(h2)/(2*a)))
    c1,c2=centre(lam1),centre(lam2)
    x=np.linspace(c1-.6,c2+.6,300)
    sigma=rng.uniform(.065,.10)
    y=1.0*g(x,c1,sigma)+.5*g(x,c2,sigma)
    y+=rng.normal(0,.018,len(x))
    centroid=np.sum(x*np.maximum(y,0))/np.sum(
        np.maximum(y,0))
    old=lam1*np.sqrt(h2)/(2*np.sin(
        np.radians(centroid/2)))
    def residual(q):
        shift,width,amp,base=q
        return (amp*g(x,shift,width)
            +amp*.5*g(x,shift+(c2-c1),width)
            +base-y)
    r=least_squares(residual,[c1,sigma,1,0],
                    bounds=([c1-.3,.03,.1,-.2],
                            [c1+.3,.2,2,.2]))
    fitted=r.x[0]
    new=lam1*np.sqrt(h2)/(2*np.sin(
        np.radians(fitted/2)))
    oldcurve=1.5*g(x,centroid,sigma)
    newcurve=r.x[2]*g(x,fitted,r.x[1])+(
        r.x[2]*.5*g(x,fitted+c2-c1,r.x[1]))+r.x[3]
    return a,old,new,x,y,oldcurve,newcurve

evaluate('Materials: XRD','Lattice parameter error (Å)',xrd)

# 2. NMR: known nuisance solvent/water peak versus
# assigning every peak to the analyte.
def nmr():
    target=rng.uniform(3.5,5.5)
    nuisance=rng.uniform(.5,2.0)
    x=np.linspace(1.3,2.3,400)
    y=target*g(x,2.05,.018)+nuisance*g(x,1.56,.018)
    y+=rng.normal(0,.035,len(x))
    old=np.trapezoid(y,x)/(
        np.sqrt(2*np.pi)*.018)
    mask=np.abs(x-2.05)<.10
    new=np.trapezoid(y[mask],x[mask])/(
        np.sqrt(2*np.pi)*.018)
    oldcurve=old*g(x,2.05,.018)
    newcurve=new*g(x,2.05,.018)
    return target,old,new,x,y,oldcurve,newcurve

evaluate('Chemistry: NMR','Signal amplitude error',nmr)

# 3. PL: observed peak offset from band gap.
# An assumed known thermal offset is removed.
def pl():
    T=rng.uniform(80,300)
    eg=1.519-.0005405*T*T/(T+204)
    offset=.5*8.617333262e-5*T
    peak=eg-offset
    x=np.linspace(1.25,1.58,400)
    width=.014
    y=g(x,peak,width)+rng.normal(0,.02,len(x))
    observed=x[np.argmax(y)]
    old=observed
    new=observed+offset
    return eg,old,new,x,y,g(x,old,width),g(x,new-offset,width)

evaluate('Physics: PL','Band-gap error (eV)',pl)

# 4. Astronomy: blended H-alpha + [N II] triplet.
def astro():
    z=rng.uniform(.03,.06)
    x=np.linspace(6500*(1+z),6630*(1+z),450)
    centres=np.array([6549.86,6564.61,6585.27])*(1+z)
    ha=rng.uniform(5,12)
    nii=rng.uniform(2,6)
    s=rng.uniform(2.3,4.5)
    y=(nii/2.96*g(x,centres[0],s)
       +ha*g(x,centres[1],s)
       +nii*g(x,centres[2],s))
    y+=rng.normal(0,.06,len(x))
    # Naive fixed-aperture flux estimates; contamination
    # from neighbours is deliberately not corrected.
    def aperture(c):
        m=np.abs(x-c)<8
        return np.trapezoid(y[m],x[m])
    old=aperture(centres[2])/aperture(centres[1])
    def residual(q):
        h,n,width=q
        return (n/2.96*g(x,centres[0],width)
                +h*g(x,centres[1],width)
                +n*g(x,centres[2],width)-y)
    fit=least_squares(
        residual,[ha,nii,3.5],
        bounds=([.1,.1,1],[30,30,8]))
    h,n,width=fit.x
    new=n/h
    oldcurve=(aperture(centres[1])/
              (s*np.sqrt(2*np.pi)))*g(
                  x,centres[1],s)
    newcurve=(n/2.96*g(x,centres[0],width)
              +h*g(x,centres[1],width)
              +n*g(x,centres[2],width))
    return nii/ha,old,new,x,y,oldcurve,newcurve

evaluate('Astronomy: emission lines',
         '[N II]/H-alpha ratio error',astro)

# 5. SAW: finite-size estimate versus correction
# using the known critical exponent.
def saw():
    mu=2.6381585303279
    gamma=43/32
    n=int(rng.integers(18,65))
    # Synthetic asymptotic counts, not exact SAW enumeration.
    nn=np.arange(2,n+1)
    correction=rng.uniform(-.1,.1)
    counts=mu**nn * nn**(gamma-1)*(
        1+correction/nn)
    old=counts[-1]/counts[-2]
    new=old/((n/(n-1))**(gamma-1))
    xx=nn[-12:]
    yy=counts[-12:]/counts[-13:-1]
    oldcurve=np.full(len(xx),old)
    newcurve=np.full(len(xx),new)
    return mu,old,new,xx,yy,oldcurve,newcurve

evaluate('Mathematics: walks','Growth constant error',saw)

with (O/'benchmark_cases.csv').open('w',newline='') as f:
    w=csv.writer(f)
    w.writerow(['domain','trial','truth','without','with',
                'without_abs_error','with_abs_error'])
    w.writerows(records)

# Cross-domain summary: dimensionless relative reduction
fig,ax=plt.subplots(figsize=(10,5.6))
names=[v[0].split(':')[0] for v in figures]
vals=[v[2] for v in figures]
low=[v[2]-v[3][0] for v in figures]
high=[v[3][1]-v[2] for v in figures]
y=np.arange(5)
ax.barh(y,vals,color=[
    '#087d64' if v>=0 else '#b46c54' for v in vals
])
ax.errorbar(vals,y,xerr=[low,high],fmt='none',
            ecolor='black',capsize=4)
ax.axvline(0,color='black',lw=.9)
ax.set_yticks(y,names)
ax.invert_yaxis()
ax.set_xlabel('Mean absolute-error reduction (%)')
ax.set_title('Five-domain synthetic pilot',
             fontsize=16,fontweight='bold')
ax.grid(axis='x',alpha=.15)
ax.set_axisbelow(True)
fig.tight_layout()
summary=O/'summary.png'
fig.savefig(summary,dpi=200,bbox_inches='tight')
plt.close(fig)

styles=getSampleStyleSheet()
doc=SimpleDocTemplate(
    str(O/'OSI_Supplement.pdf'),
    pagesize=(595,842),
    rightMargin=42,leftMargin=42,
    topMargin=38,bottomMargin=38
)
story=[
    Paragraph('Cross-domain analysis: supplementary results',
              styles['Title']),
    Spacer(1,12),
    Paragraph(
        'Paired synthetic pilot, 100 trials per field. '
        'Without and With use the same observation; With '
        'adds a domain-specific physical constraint or '
        'reference correction. Improvements are reductions '
        'in mean absolute parameter error, not classification '
        'accuracy or real-world validation.',
        styles['BodyText']
    ),
    Spacer(1,16)
]
for name,fn,delta,ci,n in figures:
    story.append(PageBreak())
    story.append(Paragraph(name,styles['Heading1']))
    story.append(Spacer(1,14))
    story.append(Image(str(fn),width=505,height=197))
    story.append(Spacer(1,16))
    story.append(Paragraph(
        f'Mean error reduction: {delta:+.1f}% '
        f'(paired bootstrap 95% interval '
        f'{ci[0]:+.1f}% to {ci[1]:+.1f}%; '
        f'n={n}).',
        styles['BodyText']
    ))
    story.append(Spacer(1,14))
    story.append(Paragraph(
        'Synthetic proof of concept. This does not establish '
        'held-out performance of the full RamanLens system.',
        styles['Italic']
    ))
story.append(PageBreak())
story.append(Paragraph('Summary',styles['Heading1']))
story.append(Image(str(summary),width=505,height=283))
story.append(Spacer(1,14))
story.append(Paragraph(
    'All five results are paired synthetic method comparisons. '
    'They use different scientific quantities and deliberately '
    'simplified models. The published Raman held-out benchmark '
    'must be reported separately rather than pooled with these '
    'five error-reduction percentages.',
    styles['BodyText']
))
doc.build(story)
print('PDF:',O/'OSI_Supplement.pdf')
print('Summary:',summary)
