import React, { memo } from 'react';
import { ZoomableGroup, ComposableMap, Geographies, Geography } from 'react-simple-maps';
import countries from './countries.json';
import './styles.css';

const seaCountriesColors: Record<string, string> = {
  Philippines: '#FF0000', // Red
  Indonesia: '#FF6B6B', // Light red
  Japan: '#8B0000', // Dark red
  Malaysia: '#FF4500', // Orange red
  Singapore: '#DC143C', // Crimson
};

type MapChartProps = {
  setTooltipContent: (content: string) => void;
  sliderValue: number[];
};

const MapChart = ({ setTooltipContent, sliderValue }: MapChartProps) => {
  return (
    <div>
      <ComposableMap>
        <ZoomableGroup>
          <Geographies geography={countries}>
            {({ geographies }: { geographies: any[] }) =>
              geographies.map((geo: any) => (
                <Geography
                  key={geo.rsmKey}
                  geography={geo}
                  data-tooltip-id="geography-tooltip"
                  onMouseEnter={() => {
                    setTooltipContent(`${geo.properties.name}`);
                  }}
                  onMouseLeave={() => {
                    setTooltipContent('');
                  }}
                  style={{
                    default: {
                      fill:
                        sliderValue[0] === 20 && seaCountriesColors[geo.properties.name]
                          ? seaCountriesColors[geo.properties.name]
                          : '#D6D6DA',
                      outline: 'none',
                    },
                    hover: {
                      fill: '#F53',
                      outline: 'none',
                    },
                    pressed: {
                      fill: '#E42',
                      outline: 'none',
                    },
                  }}
                />
              ))
            }
          </Geographies>
        </ZoomableGroup>
      </ComposableMap>
    </div>
  );
};

export default memo(MapChart);
