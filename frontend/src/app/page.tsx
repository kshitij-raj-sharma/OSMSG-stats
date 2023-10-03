// components/CSVReader
"use client";

import React, { useEffect, useState } from "react";
import SimpleLineChart from "@/components/Charts/SimpleLineChart";
import * as XLSX from "xlsx";

const Home = () => {
  const [data, setData] = useState<any | null>(undefined);
  const [csvData, setCsvData] = useState<any | null>(undefined);
  const [csvDataNepal, setCsvDataNepal] = useState<any | null>(undefined);
  useEffect(() => {
    const fetchFileForTurkey = async () => {
      try {
        const response = await fetch(
          "https://raw.githubusercontent.com/kshitijrajsharma/OSMSG/master/stats/turkeyeq/Daily/stats_summary.csv"
        ); // Replace 'example.xls' with your file name
        const responseData = await response.arrayBuffer();
        const workbook = XLSX.read(new Uint8Array(responseData), {
          type: "array",
        });
        const sheetName = workbook.SheetNames[0];
        const worksheet = workbook.Sheets[sheetName];
        const jsonData = XLSX.utils.sheet_to_json(worksheet, {
          raw: false,
          // dateNF: "dd/mm/YYYY"
        });
        const normalizedDatax = jsonData?.map((row: any) => {
          if (row.editors === undefined) return {};
          const parsedEditors = JSON?.parse(row.editors);
          const keys = Object.keys(parsedEditors);
          return {
            name: row.timestamp,
            josm: parsedEditors.josm,
            rapid: parsedEditors["rapid "],
            id: parsedEditors["id "],
            users: +row["users"],
          };
        });
        setCsvData(normalizedDatax);
      } catch (error) {
        console.log(error, "error");
        console.error("Error fetching or reading the file:", error);
      }
    };
    const fetchFileForNepal = async () => {
      try {
        const response = await fetch(
          "https://raw.githubusercontent.com/kshitijrajsharma/OSMSG/master/stats/Nepal/Weekly/stats_summary.csv"
        ); // Replace 'example.xls' with your file name
        const responseData = await response.arrayBuffer();
        const workbook = XLSX.read(new Uint8Array(responseData), {
          type: "array",
        });
        const sheetName = workbook.SheetNames[0];
        const worksheet = workbook.Sheets[sheetName];
        const jsonData = XLSX.utils.sheet_to_json(worksheet, {
          raw: false,
          // dateNF: "dd/mm/YYYY"
        });
        const normalizedDatax = jsonData?.map((row: any) => {
          if (row.editors === undefined) return {};
          const parsedEditors = JSON?.parse(row.editors);
          const keys = Object.keys(parsedEditors);
          return {
            name: row.timestamp,
            josm: parsedEditors.josm,
            rapid: parsedEditors["rapid "],
            id: parsedEditors["id "],
            users: +row["users"],
          };
        });
        setCsvDataNepal(normalizedDatax);
      } catch (error) {
        console.log(error, "error");
        console.error("Error fetching or reading the file:", error);
      }
    };

    fetchFileForTurkey();
    fetchFileForNepal();
  }, []);

  return (
    <div>
      <SimpleLineChart data={csvData} chartTitle="Daily Stats for Turkey" />;
      <SimpleLineChart data={csvDataNepal} chartTitle="Daily Stats for Nepal" />
      ;
    </div>
  );
};

export default Home;
