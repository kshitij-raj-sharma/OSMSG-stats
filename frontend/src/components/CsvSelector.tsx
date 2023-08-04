// components/CSVSelector.tsx
import React from "react";

type Props = {
    onChange(data: string[][]): void;
};

const CSVSelector = ({ onChange }: Props) => {
    const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files) {
            try {
                const file = e.target.files[0];

                // 1. create url from the file
                const fileUrl = URL.createObjectURL(file);

                // 2. use fetch API to read the file
                const response = await fetch(fileUrl);

                // 3. get the text from the response
                const text = await response.text();

                // 4. split the text by newline
                const lines = text.split("\n");

                // 5. map through all the lines and split each line by comma.
                const _data = lines.map((line) => line.split(","));

                // 6. call the onChange event
                onChange(_data);
            } catch (error) {
                console.error(error);
            }
        }
    };

    return <input type="file" accept=".csv" onChange={handleFileChange} />;
};

export default CSVSelector;