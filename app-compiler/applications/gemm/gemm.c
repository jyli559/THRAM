#include <string.h>
#include <stdio.h>


#define SIZE  10
int n = SIZE;
int A[SIZE][SIZE], B[SIZE][SIZE], C[SIZE][SIZE];
int i,j;
void gemm(){
   int i,j,k;

   for (i=0;i<SIZE; i++)
      for (j=0; j<SIZE; j++)
         for (k=0;k<SIZE; k++){
            #ifdef CGRA_COMPILER
               please_map_me();
            #endif
            A[i][j] = A[i][j] + B[i][k]* C[k][j];
         }
}

void main(){

int i,j;
for (i=0;i<n; i++)
   for (j=0; j<n; j++) {
      A[i][j]=0;
      B[i][j] = j+i;
      C[i][j] = j*i;
    }
    
gemm();

for (i=0;i<n; i++)
   for (j=0; j<n; j++) {
      printf("%d\n", A[i][j]);
    }

}


