# PEST: Programmable Experimental Sample Tree
Author: Willis O'Leary (wolearyc[at]mit.edu)
### Motivation
Typically, we keep track of laboratory samples in a linear laboratory notebook or spreadsheet. However, when samples derive themselves from other samples, bookkeeping becomes complicated and unintutive. Furthermore, storage of sample information on paper (or in a program like Microsoft Excel) robs us of the ability to perform complicated data analysis. To solve this problem, I have developed pest. 

### Overview 
pest serves as an electronic suplement to a laboratory notebook. With pest, you can keep track of each of your sample's unique history. Every day, you can tell pest what you did in lab. Pest will then automatically build a sort of "family tree" for all of your samples. In addition, pest will provide automatic sample IDs and human-readable sample labels so you can keep track of everything. 

Pest goes further, also keeping track of all your data for each sample. Eventually, I'd like to integrate automatic data analysis and even machine learning into the system. 

### Data Modules
Data modules exist to both keep track of and perform automatic analyses on data. At minimum, a data module has some user-recognizeable name (e.g. xrd) and some sort of directory formula which it applies to find the data. Optionally, a data module can determine if it is relevant for a certain sample.