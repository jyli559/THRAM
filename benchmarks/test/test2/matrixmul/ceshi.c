#include<stdio.h>
int main()
{
    int i = 0;
    char port[10];
    sprintf(port,"%s%d","input",i);
    printf("%s\n",port);
    i++;
    sprintf(port,"%s%d","input",i);
    printf("%s",port);
}
