import { chunk, range } from "lodash";
import Link from "next/link";
import Head from "next/head";
import React from "react";
import styled from "styled-components";

const size = 4;

const taskNames = ["Pipetting", "Colony Count", "Mini-Prep", "Glycerol Stock"];

const IndexPage = () => {
  // RENDER
  return (
    <>
      <Head>
        <title>LATTICE</title>
        <meta name="description" content={"Queryable Scientific Infrastructure"} />
      </Head>
      <StyledIndexPage>
        <main>
          <div className="info">
            <h1>LATTICE</h1>
            <h2>LabJack</h2>
            <section>
              <p>
                <u>Wearable A.I. assistant for researchers and labs</u>.<br /> Voice commands for documenting work,
                video replays, internal lab knowledge base queries, and more...
                {/* <a href="https://undergroundgarden.club" target="_blank">
                  Underground Garden Club
                </a> */}
              </p>
              <p>
                If you want a LABJACK and/or to join me in building robotic infrastructure for the generative AI
                scientific revolution (so we can engineer catalysts & microbes to fight climate change), let's talk:
                <br />
                <a href="mailto:x@markthemark.com">mail</a> /{" "}
                <a href="https://www.linkedin.com/in/markdghansen/" target="_blank" rel="noreferrer">
                  linkedin
                </a>
              </p>
            </section>
          </div>
        </main>
        <div className="lattice">
          {range(0, size).map((sl, slIdx) => (
            <StyledLatticeSlice sliceIndex={slIdx}>
              <div className="lattice__slice__row__title">
                Task {4 - slIdx - 1}:<br />
                {taskNames[4 - slIdx - 1]}
              </div>
              {range(0, size).map((row, rowIdx) => (
                <div className="lattice__slice__row">
                  {range(0, size).map((col, colIdx) => (
                    <div className="lattice__slice__row__item">
                      {/* flipping order bc i like the pipettes in front */}
                      <video
                        key={`${size - (slIdx + 1)}-${rowIdx}${colIdx}`}
                        src={`/clips/${size - (slIdx + 1)}-${rowIdx}${colIdx}.mp4`}
                        autoPlay
                        loop
                        muted
                      />
                    </div>
                  ))}
                </div>
              ))}
            </StyledLatticeSlice>
          ))}
        </div>
      </StyledIndexPage>
    </>
  );
};

export const StyledIndexPage = styled.div`
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 0;
  overflow: hidden;
  background-color: #00f;
  background-image: linear-gradient(to right, #00a 1px, transparent 1px),
    linear-gradient(to bottom, #00a 1px, transparent 1px);
  background-size: 20px 20px;

  h1,
  h2 {
    font-family: "Stonewall 50";
  }
  p,
  small {
    font-family: "CoFo Rax", sans-serif;
  }

  main {
    position: fixed;
    z-index: 1;
    height: 100vh;
    width: 100%;
    .info {
      max-width: 640px;
      margin: 120px 40px 0;
      color: #0d0;
      h2 {
        font-size: 96px;
      }
      section {
        max-width: 480px;
      }
      p {
        margin: 12px 0;
        font-weight: 900;
        line-height: 140%;
        color: #0f0;
        background: blue;
      }
      a {
        color: inherit;
      }
    }
  }

  .lattice {
    width: 0;
    margin: 40px 620px 0 auto;
  }

  @media (max-width: 45em) {
    main {
      .info {
        margin: 20px;
        h2 {
          font-size: 64px;
        }
      }
    }
    .lattice {
      width: 480px;
      margin: 360px auto 0;
      transform: scale(0.6);
    }
  }

  @media (min-width: 1240px) {
    main {
      .info {
        margin: 180px 180px;
        h2 {
          font-size: 140px;
        }
      }
    }
    .lattice {
      margin: 80px 820px 0 auto;
    }
  }
`;

export const StyledLatticeSlice = styled.div<{ sliceIndex: number }>`
  position: absolute;
  transform: ${(props) => {
    return `matrix3d(1.75, 0.5, 0, 0, -0.2, 1.4, 0, 0, 0, 0, 1, 0, 0, 0, 0, 2.5) translate3d(-${
      props.sliceIndex * 300 * 0.5
    }px, ${props.sliceIndex * 300 * 0.9}px, 0px);`;
  }}
  display: flex;
  .lattice__slice__row__title {
    color: #0d0;
    width: 64px;
    text-align: right;
    font-family: "Stonewall 50";
    font-size: 18px;
  }
  .lattice__slice__row__item {
    margin: 12px;
    padding: 0;
    border: 4px solid #0d0;
    background: #0d0;
    max-width: 180px;
    display: flex;
    justify-content: center;
    align-items: center;
    overflow: hidden;
    video {
      max-width: 180px;
    }
  }
`;

export default IndexPage;
