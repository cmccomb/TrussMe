[![Build Status](https://travis-ci.org/HSDL/truss-me.svg?branch=master)](https://travis-ci.org/HSDL/truss-me)

**Contributors:** {% for member in site.github.contributors %}<a href="{{member.html_url}}"><img src="{{member.avatar_url}}" width="32" height="32"></a>{% endfor %}

## Introduction 
Provides basic construction and analysis capabilities for trusses.

## Construction
Add joints and members, and vary the material and cross-section of specific members in the truss. There is also an option to create truss from <code>.trs</code> file

## Analysis
Calculate mass, forces, and the factor of safety (FOS) against buckling and yielding. Create a truss analysis report that provides approximate design recommendations

### Acknowledgements
Force calculations based on a MATLAB function by [Hossein Rahami](http://www.mathworks.com/matlabcentral/fileexchange/authors/27559).
