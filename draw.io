<mxfile host="app.diagrams.net">
  <diagram name="TeamAI Architecture">
    <mxGraphModel dx="1422" dy="794" grid="1" gridSize="10" guides="1">
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>

        <!-- Inputs -->
        <mxCell id="2" value="Users / Teams&#xa;• Meeting Transcripts&#xa;• Emails&#xa;• Ask AI Queries"
        style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;"
        vertex="1" parent="1">
          <mxGeometry x="40" y="220" width="200" height="120" as="geometry"/>
        </mxCell>

        <!-- Core Platform -->
        <mxCell id="3" value="TeamAI Intelligence Platform"
        style="rounded=1;whiteSpace=wrap;html=1;fontStyle=1;fillColor=#e1d5e7;strokeColor=#9673a6;"
        vertex="1" parent="1">
          <mxGeometry x="300" y="120" width="420" height="320" as="geometry"/>
        </mxCell>

        <mxCell id="4" value="K2-Think-V2 Reasoning&#xa;• Task Extraction&#xa;• Decisions&#xa;• Risks"
        style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f8cecc;strokeColor=#b85450;"
        vertex="1" parent="3">
          <mxGeometry x="20" y="40" width="180" height="100" as="geometry"/>
        </mxCell>

        <mxCell id="5" value="Department Context Engine&#xa;• Team Members&#xa;• Responsibilities&#xa;• Smart Assignment"
        style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;"
        vertex="1" parent="3">
          <mxGeometry x="220" y="40" width="180" height="100" as="geometry"/>
        </mxCell>

        <mxCell id="6" value="Memory &amp; State Manager"
        style="rounded=1;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;"
        vertex="1" parent="3">
          <mxGeometry x="20" y="180" width="180" height="80" as="geometry"/>
        </mxCell>

        <mxCell id="7" value="OpenClaw Orchestration&#xa;• Tool Execution&#xa;• Automation"
        style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#666666;"
        vertex="1" parent="3">
          <mxGeometry x="220" y="180" width="180" height="80" as="geometry"/>
        </mxCell>

        <!-- Storage -->
        <mxCell id="8" value="SQLite&#xa;Tasks / Decisions / Risks"
        style="shape=cylinder;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;"
        vertex="1" parent="1">
          <mxGeometry x="780" y="150" width="120" height="80" as="geometry"/>
        </mxCell>

        <mxCell id="9" value="ChromaDB&#xa;Vector Memory"
        style="shape=cylinder;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;"
        vertex="1" parent="1">
          <mxGeometry x="780" y="260" width="120" height="80" as="geometry"/>
        </mxCell>

        <mxCell id="10" value="Notion Integration&#xa;Task Sync"
        style="rounded=1;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;"
        vertex="1" parent="1">
          <mxGeometry x="950" y="200" width="150" height="100" as="geometry"/>
        </mxCell>

        <!-- Arrows -->
        <mxCell id="11" style="endArrow=block;html=1;" edge="1" parent="1" source="2" target="3">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>

        <mxCell id="12" style="endArrow=block;html=1;" edge="1" parent="1" source="3" target="8">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>

        <mxCell id="13" style="endArrow=block;html=1;" edge="1" parent="1" source="3" target="9">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>

        <mxCell id="14" style="endArrow=block;html=1;" edge="1" parent="1" source="3" target="10">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>

      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
