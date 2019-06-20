# PEST: Programmable Experimental Sample Tree
Author: Willis O'Leary (wolearyc[at]mit.edu)
### Motivation
Typically, we keep track of laboratory samples in a linear laboratory notebook or spreadsheet. However, when samples derive themselves from other samples, bookkeeping with these tools is complicated and unintuitive. Additionally, storage of sample information on paper (or in a program like Microsoft Excel) robs us of the ability to perform complicated data analysis. Finally, storage using these mediums separates sample information from experimental data. To partially resolve these problems, I present pest. 

### Overview 
pest serves as an electronic supplement to a laboratory notebook. With pest, you can keep track of each of your samples' unique histories. Every day, you tell pest what you did in lab. Pest will then automatically build a sort of "family tree" for all of your samples. In addition, pest will provide sample IDs and human-readable sample labels (to your specifications) so you can keep track of everything. Pest goes further, also keeping track of all your data for each sample. This framework can hook onto data analysis routines as well. 

### Data Modules
Data modules exist to both keep track of and perform automatic analyses on data. At minimum, a data module has some user-recognizable name (e.g. xrd) and some sort of directory formula which it applies to find the data. Optionally, a data module can determine if it is relevant for a certain sample.