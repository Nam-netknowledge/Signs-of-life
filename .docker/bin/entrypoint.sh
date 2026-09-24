#!/bin/bash
#
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color
#
PROCCESS_DIR='data/*.csv'

CONTAINER_NAME=$(hostname)

crawl_dir () {
    for file in $PROCCESS_DIR
    do
        # unquoted glob with no match expands to the literal pattern string;
        # skip that case instead of trying to process a nonexistent file
        # (this script runs under /bin/sh, so 'shopt -s nullglob' isn't available here)
        [ -e "$file" ] || continue
        echo -e "\n\n*****************\n\n"
        echo -e "* ${BLUE}Input file found [${file}]${NC}";
        #
        if [ "$(sed -n '/^url/p;q' "${file}")" ] 
        then
            echo -e "* ${GREEN}found URL in file [${file}] - Crawling.${NC}"
            BASENAME=$(basename "$file")
            mkdir -p $input_folder
            mkdir -p $input_folder/${CONTAINER_NAME}
            mv "$file" $input_folder/${CONTAINER_NAME}
            python -u app_domains/main_domains.py -container_name="${CONTAINER_NAME}"
            EXIT_CODE=$?
            if [ $EXIT_CODE -eq 0 ]; then
                mkdir -p done
                mv "$input_folder/${CONTAINER_NAME}/$BASENAME" done/
                rm  $input_folder/${CONTAINER_NAME}/$BASENAME.chunk*
            else
                echo -e "* ${RED}main_domains.py exited with code ${EXIT_CODE} for [${BASENAME}] - leaving file and chunks in place for retry next cycle.${NC}"
            fi
        else
            echo -e "* ${RED}no URL found in file [${file}] - skipping.${NC}"
        fi
    done
    for file in $input_folder/$CONTAINER_NAME/*.csv
    do
        BASENAME=$(basename "$file")
        case "$BASENAME" in
            *chunk*) 
                ;;  # Do nothing if "chunk" is found
            "*.csv")
                ;;  # Do nothing if no file was found
            *)
                # Execute if a non-chunk is not found
                echo "${GREEN}File found in processing $BASENAME - Crawling. ${NC}"
                python -u app_domains/main_domains.py -container_name="${CONTAINER_NAME}"
                EXIT_CODE=$?
                if [ $EXIT_CODE -eq 0 ]; then
                    mkdir -p done
                    mv "$input_folder/${CONTAINER_NAME}/$BASENAME" done/
                    rm  $input_folder/${CONTAINER_NAME}/$BASENAME.chunk*
                else
                    echo -e "* ${RED}main_domains.py exited with code ${EXIT_CODE} for [${BASENAME}] - leaving file and chunks in place for retry next cycle.${NC}"
                fi
                ;;
        esac
    done
    echo -e "\n\n*****************\n\n"
}

main () {
   while true
   do
       echo -e "* ${BLUE}Looking for input files to Crawl in [${PROCCESS_DIR}].${NC}";
       crawl_dir
       echo -e "* ${BLUE}Done Crawling. Going to Sleep.....${NC}";
       sleep 60s
   done
}

echo -e "* ${BLUE}Starting the Crawler. ID: ${CONTAINER_NAME}${NC}";
main
echo -e "* ${BLUE}Bye Bye....!${NC}";

#ping 127.0.0.1