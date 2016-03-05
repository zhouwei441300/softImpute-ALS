
from sklearn import preprocessing
import scipy.sparse as sps
import scipy
from scipy import linalg
import numpy as np
#import matplotlib.pyplot as plt
import time
import random


# data file
movielens100k="movielens/u.data"


def generate_training_dataset(filename):
  array=np.genfromtxt(filename,dtype="int")
  population_size=len(array)
  population_indices=np.arange(population_size)
  training_indices=random.sample(population_indices,int(population_size*0.8))
  training_array=array[training_indices]
  np.savetxt("training_dataset",training_array,delimiter="\t")
  
def loadMatrix(filename):
  array=np.genfromtxt(filename)
  userID=array[:,0]
  movieID=array[:,1]
  values=array[:,2]
  X=sps.coo_matrix((values,(userID-1,movieID-1)),shape=(943,1682))
  #X=sps.coo_matrix((values,(userID-1,movieID-1)),shape=(6040,3952))
  #returns a coo_matrix X
  return X

def Frob(Uold,Dsqold,Vold,U,Dsq,V):
  denom=sum(Dsqold**2)
  utu=Dsq* ((U.T).dot(Uold))
  vtv=Dsqold* ((Vold.T).dot(V))
  uvprod= sum(diag(utu.dot(vtv)))
  num=denom+sum(Dsq**2) -2*uvprod
  num = num/max(denom,1e-9)
  return num
  

# Algorithm 3.1
def main():
  print "loading matrix X"
  X=loadMatrix(movielens100k)
  print("load data from movielens100k")
  print(X)

  m,n=np.shape(X)
  # r is the rank
  r=5
  #Lambda is the regularization parameter
  Lambda=40
  # 1.initialize matrix U
  #m>>r

  print "creating U"
  #U is an mxr matrix
  U = np.random.randn(m, r)
  #Calling QR Factorization on U
  print "QR Factorization"
  Q,R = linalg.qr(U)
  U=Q[:,0:r]
  #U is now a matrix with orthonormal columns
  
  #D is an rxr identity matrix of type numpy.ndarray
  D=np.identity(r)
  Dsq=D**2  
  A=U.dot(D)

  #V is nxr
  V=np.zeros(n*r).reshape(n,r)
  #B is an nxr matrix
  B=V.dot(D)

  print "changing X to dok_matrix"
  
  #X=X.tocsr()
  #Xt=X.transpose()
  #Omega is the <'list'> of coordinates with nonzero entries

  print "obtaining Omega"
  X=X.todok()
  print("X todok")
  print(X)
  Omega=X.keys()
  row=[o[0] for o in Omega]
  col=[o[1] for o in Omega]
  #Omegat=Xt.keys()
  
  X=X.todense()
  print("X todense")
  print(X)

  # ----
  xnas = [y == 0 for y in X ]
  print("NA vals")
  print(xnas)

  nz=m*n-sum(xnas)
  xfill = X[:]
  #xfill[xnas]=0
  #---
  print "setting threshold"
  threshold=10**(-6)
  iterations=0
  
  # tempx is a copy of the sparse matrix to be used as Xstar
  #tempx=sps.coo_matrix(X)
  #tempx=tempx.todense()
  tempx=X
  t=time.time()

  print("X preprocessing.scale")
  print(X)

  while(True):
    U_old=U
    V_old=V
    Dsq_old=Dsq

    ## U step

    #B=t(U)%*%xfill
    B=np.dot(U.T, xfill)
    #if(lambda>0)B=B*(Dsq/(Dsq+lambda))
    dsqRatio = np.divide(Dsq,Dsq+Lambda)
    B=np.dot(B, dsqRatio)
    #Bsvd=svd(t(B))
    u,d,v=linalg.svd(B.T)
    #V=Bsvd$u
    V=u
    #Dsq=(Bsvd$d)
    Dsq = np.diagflat(d)
    #U=U%*%Bsvd$v
    U=np.dot(U,v)
    #xhat=U %*%(Dsq*t(V))
    Xstar=np.dot(U, Dsq*(V.T))
    #xfill[xnas]=xhat[xnas]
    #xfill[xnas]=Xstar[xnas]


    ###The next line we could have done later; this is to match with sparse version
    # if(trace.it) obj=(.5*sum( (xfill-xhat)[!xnas]^2)+lambda*sum(Dsq))/nz
    obj=(.5*sum((xfill-Xstar)[xnas==False]**2)+Lambda*sum(d))/nz
    
    ## V step
    
    #A=t(xfill%*%V)
    A=(np.dot(xfill,V)).T
    #if(lambda>0)A=A*(Dsq/(Dsq+lambda))
    A=np.dot(A, np.divide(Dsq,(Dsq+Lambda)))
    #Asvd=svd(t(A))
    U,d,V=svd(A.T)
    #U=Asvd$u
    #Dsq=Asvd$d
    Dsq=np.diagflat(np.sqrt(d))
    #V=V %*% Asvd$v
    V=V.dot(linalg.svd(A,V))
    #xhat=U %*%(Dsq*t(V))
    Xstar=U.dot(Dsq.dot(V.T))
    #xfill[xnas]=xhat[xnas]
    xfill[xnas]=Xstar[xnas]
    ratio=Frob(U.old,Dsq.old,V.old,U,Dsq,V)
    ratio=np.linalg.norm('fro')
    #if(trace.it) cat(iter, ":", "obj",format(round(obj,5)),"ratio", ratio, "\n")
  
      

    #plt.scatter(time.time()-t,Delta_B,c="red")
    
    
    iterations+=1
    print "number of iterations: " +str(iterations)
    #if(iter==maxit)warning(paste("Convergence not achieved by",maxit,"iterations"))
    
    # plotting the convergence rate
    #plt.scatter(time.time()-t,Delta_A,c="blue")
    

    #we break the loop upon convergence
    #if((ratio > thresh)and(iter<maxit))
    if(ratio > threshold):
      break
    print "threshold not reached, continue"
    
    
  #plt.title("Regularization Lambda is: "+str(Lambda) +"  rank is: " +str(r))
 # plt.show()
  
  Bt=B.T

  ABt=A.dot(Bt)

  for cood in Omega:
      i,j=cood
      X[i,j] = X[i,j]-ABt[i,j]
      
  Xstar=X+ABt
  M=Xstar.dot(V)
  U,D,Rt=linalg.svd(M,full_matrices=False)
  V=V.dot(Rt.T)
  #threshold the matrix D
  threshold_lambda=40
  D=np.maximum(D-threshold_lambda,0)
  print D
  D=np.diagflat(D)
  
  print "D is:"
  print D
 
  full_matrix=(U.dot(D**2)).dot(V.T)
  #full_matrix=preprocessing.scale(full_matrix)
  np.savetxt("Full Matrix", full_matrix,delimiter=" ",fmt="%d")

if __name__ == '__main__':
  main()