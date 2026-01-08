#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define DATABASE_FILE_NAME "queried_name.txt"

// Return 1 if string starts with substring, 0 else
int starts_with(char *substring, char *string)
{
    return strncmp(substring, string, strlen(substring)) == 0;
}

int exists(const char *fname)
{
    FILE *file;
    if ((file = fopen(fname, "r")))
    {
        fclose(file);
        return 1;
    }
    return 0;
}

int main(int argc, char *argv[])
{
    if (argc < 2)
    {
        fprintf(stderr, "[ERROR] Missing argument : username\n");
        fprintf(stdout, "USAGE : ./superDB <username\n");
        exit(-1);
    }
    char *username = argv[1];
    char * mode = exists(DATABASE_FILE_NAME) ? "r+" : "w";
    FILE *f = fopen(DATABASE_FILE_NAME, mode);
    if (f == NULL)
    {
        fprintf(stderr, "[ERROR] Unable to open file in read mode : %s\n", DATABASE_FILE_NAME);
        exit(-1);
    }

    int nb_queries = 0;
    char line[200];
    char * new_file_data = (char *) malloc(sizeof(char)*2000);
    char * ptr = new_file_data;
    int found = 0;

    while (fgets(line, 200, f) != NULL)
    {
        if (starts_with(username, line))
        {
            int i = 0;
            while(i<strlen(line) && line[i] != ':' ) { i++; }
            line[i] = 0;
            sscanf(&(line[i+1]), "%d", &nb_queries);
            if(nb_queries == 0) {
                printf("[WARNING] Could not parse query count for username %s , setting to zero", line);
            }
            printf("Current number queries is %d\n", nb_queries);
            nb_queries += 1;
            int nb_written = sprintf(ptr, "%s:%d\n", line, nb_queries);
            ptr += nb_written;
            found = 1;
            
        } else {
            strcpy(ptr, line);
            ptr += strlen(line);
        }
    }
    if(!found) {
        sprintf(ptr, "%s:1\n", username);
    }
    fseek(f, 0, SEEK_SET);
    fwrite(new_file_data, 1, strlen(new_file_data), f);
    return nb_queries;
}