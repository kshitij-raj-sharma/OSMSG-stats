import React, { SyntheticEvent, useEffect, useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
} from "recharts";

interface Data {
  name: string;
  rapid: number;
  josm: number;
  id: number;
}

const SimpleLineChart: React.FC<{ data: Data[]; chartTitle: string }> = ({
  data,
  chartTitle,
}) => {
  const [tooltip, setTooltip] = useState<null>(null);
  const [point, setPoints] = useState(null);

  const CustomTooltip = ({ payload }: any) => {
    if (payload) {
      return (
        <div className="flex justify-center items-center bg-secondary-800 text-black w-40 h-32">
          <p>{payload[0]?.value}</p>
        </div>
      );
    }
    return null;
  };
  interface CustomMouseEvent extends React.MouseEvent<HTMLDivElement> {
    cx: number; // Assuming 'cx' is a number
    cy: number; // Assuming 'cx' is a number
  }
  //   const updateTooltip = (e: CustomMouseEvent) => {
  //     let x = Math.round(e.cx);
  //     let y = Math.round(e.cy);

  //     tooltip.style.opacity = "1";
  //     tooltip.style.transform = `translate(${x}px, ${y}px)`;
  //     tooltip.childNodes[0].innerHTML = e.value;
  //   };

  //   const onChartMouseMove = (chart) => {
  //     if (chart.isTooltipActive) {
  //       if (point) {
  //         setPoints(point);
  //         updateTooltip(chart);
  //       }
  //     }
  //   };

  const onChartMouseLeave = (e: Event) => {
    setPoints(null);
    // updateTooltip(e);
  };
  const totalDataCount = data
    ?.filter((d) => Object.keys(d).length !== 0)
    ?.reduce((a, b) => a + b.josm, 0);
  console.log(totalDataCount);

  return (
    <div className="flex caption2 flex-col ui-chart m-10">
      <div className="ml-24 flex justify-center flex-col w-48 items-center mt-32 mb-10">
        <p className="caption2">{chartTitle} </p>
        <p className="subheading2">{totalDataCount}</p>
      </div>
      <LineChart width={650} height={300} data={data}>
        <CartesianGrid vertical={false} opacity="0.2" />
        <XAxis
          tick={{ fill: "black" }}
          axisLine={false}
          tickLine={false}
          dataKey="name"
        />
        <YAxis
          tickCount={7}
          axisLine={false}
          tickLine={false}
          tick={{ fill: "black" }}
          type="number"
          domain={[0, 100]}
        />
        <Tooltip
          // content={<CustomTooltip />}
          viewBox={{ x: 0, y: 0, width: 20, height: 20 }}
          cursor={false}
          // position="top"
          wrapperStyle={{ display: "hidden" }}
        />
        <Legend verticalAlign="top" height={36} />
        <Line
          fill="#40C0C0"
          stroke="#60B760"
          dot={false}
          type="monotone"
          dataKey="rapid"
          strokeWidth={2}
          // activeDot={(e) => {
          //     onChartMouseMove(e);
          //     onChartMouseLeave(e);
          // }}
        />
        <Line
          fill="#40C0C0"
          stroke="#FF9E4A"
          dot={false}
          type="monotone"
          dataKey="josm"
          strokeWidth={2}
          // activeDot={(e) => {
          //     onChartMouseMove(e);
          //     onChartMouseLeave(e);
          // }}
        />
        <Line
          fill="#40C0C0"
          stroke="#5698C6"
          dot={false}
          type="monotone"
          dataKey="id"
          strokeWidth={2}
        />
        {/* <Line
                    fill="#40C0C0"
                    stroke="#5698C6"
                    dot={false}
                    type="monotone"
                    dataKey="users"
                    // activeDot={(e) => {
                    //     onChartMouseMove(e);
                    //     onChartMouseLeave(e);
                    // }}
                    strokeWidth={4}
                /> */}
      </LineChart>
      {/* <div
        className="ui-chart-tooltip text-white flex items-center justify-center"
        ref={(ref) => setTooltip(ref)}
      >
        <div className="ui-chart-tooltip-content"></div>
      </div> */}
    </div>
  );
};

export default SimpleLineChart;
