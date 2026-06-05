from fpdf import FPDF

BLUE = (27, 58, 92)
BLACK = (26, 26, 26)
GREY = (100, 100, 100)
LIGHT_LINE = (200, 200, 200)

class PDF(FPDF):
    def header(self):
        pass

    def footer(self):
        self.set_y(-15)
        self.set_font("DejaVu", "I", 8)
        self.set_text_color(*GREY)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

    def section_divider(self):
        self.ln(3)
        self.set_draw_color(*LIGHT_LINE)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(5)

    def heading1(self, text):
        self.set_font("DejaVu", "B", 16)
        self.set_text_color(*BLUE)
        self.multi_cell(0, 8, text)
        self.set_draw_color(*BLUE)
        self.line(self.l_margin, self.get_y() + 1, self.w - self.r_margin, self.get_y() + 1)
        self.ln(6)

    def heading2(self, text):
        self.set_font("DejaVu", "B", 12)
        self.set_text_color(*BLUE)
        self.multi_cell(0, 7, text)
        self.ln(2)

    def heading3(self, text):
        self.set_font("DejaVu", "B", 10.5)
        self.set_text_color(44, 95, 138)
        self.multi_cell(0, 6, text)
        self.ln(2)

    def meta_line(self, label, value):
        self.set_font("DejaVu", "B", 10)
        self.set_text_color(*BLACK)
        w = self.get_string_width(label) + 2
        self.cell(w, 6, label)
        self.set_font("DejaVu", "", 10)
        self.cell(0, 6, value)
        self.ln(6)

    def body_text(self, text):
        self.set_font("DejaVu", "", 10)
        self.set_text_color(*BLACK)
        self.multi_cell(0, 5.5, text)
        self.ln(2)

    def bold_body(self, label, text):
        self.set_font("DejaVu", "B", 10)
        self.set_text_color(*BLACK)
        w = self.get_string_width(label) + 2
        self.cell(w, 5.5, label)
        self.set_font("DejaVu", "", 10)
        x = self.get_x()
        available = self.w - self.r_margin - x
        self.multi_cell(available, 5.5, text)
        self.ln(1)

    def bullet(self, bold_part, rest):
        self.set_font("DejaVu", "", 10)
        self.set_text_color(*BLACK)
        x0 = self.l_margin + 4
        self.set_x(x0)
        self.cell(4, 5.5, chr(8226) + " ")
        x = self.get_x()
        if bold_part:
            self.set_font("DejaVu", "B", 10)
            self.write(5.5, bold_part)
            self.set_font("DejaVu", "", 10)
        if rest:
            self.write(5.5, rest)
        self.ln(7)

    def sub_bullet(self, text):
        self.set_font("DejaVu", "", 9.5)
        self.set_text_color(*BLACK)
        x0 = self.l_margin + 12
        self.set_x(x0)
        self.cell(4, 5, "- ")
        x = self.get_x()
        available = self.w - self.r_margin - x
        self.multi_cell(available, 5, text)
        self.ln(1)

    def action_label(self, text):
        self.set_font("DejaVu", "B", 10)
        self.set_text_color(44, 95, 138)
        self.multi_cell(0, 6, text)
        self.ln(1)


pdf = PDF("P", "mm", "A4")
pdf.alias_nb_pages()
pdf.set_auto_page_break(auto=True, margin=20)
pdf.add_font("DejaVu", "", "C:/Windows/Fonts/arial.ttf", uni=True)
pdf.add_font("DejaVu", "B", "C:/Windows/Fonts/arialbd.ttf", uni=True)
pdf.add_font("DejaVu", "I", "C:/Windows/Fonts/ariali.ttf", uni=True)
pdf.add_page()
pdf.set_left_margin(20)
pdf.set_right_margin(20)

pdf.heading1("Climate Action, Biodiversity and Environment SPC\nMeeting Summary")
pdf.meta_line("Date:", "Monday 23rd February 2026")
pdf.meta_line("Location:", "Dunleer, Co. Louth")
pdf.meta_line("Reported by:", "Thom Conaty - Social Inclusion PPN Representative")
pdf.section_divider()

pdf.heading2("Brief Summary")
pdf.body_text(
    "The committee received a detailed presentation on the PEACEPLUS-funded CMAP programme "
    "(EUR 9.6m, 2025-2029), a major cross-border coastal monitoring initiative designating "
    "Dundalk as a Saltmarsh Centre of Excellence, with direct relevance to Carlingford Lough, "
    "Dundalk Bay, and Baltray. January 2026 flooding highlighted a significant gap in council "
    "water pumping capabilities, with members pressing for dedicated council equipment rather "
    "than sole reliance on the Fire Brigade."
)
pdf.bullet("", "CMAP Marine Project Officer post advertised by Louth County Council")
pdf.bullet("", "Biodiversity Action Plan, Tree Management Strategy, and Community Gardens Strategy all commenced")
pdf.bullet("", "CLIMAAX risk assessment and Pesticide Use Policy presentations forthcoming")
pdf.bullet("", "National Tree Week (8th-15th March): up to 1,200 native trees available to landowners free of charge")
pdf.bullet("", "SuDS training being rolled out across all local authorities")
pdf.bullet("", "Omeath modernisation: EV charging ducting laid but ports not yet installed")
pdf.bullet("", "No public EV charger in Dunleer; follow-up agreed with Infrastructure SPC on EV Officer appointment")
pdf.bullet("", "Mid-Programme Review scheduled for Q4 2026")
pdf.section_divider()

pdf.heading2("1. Omeath Electric Charging Availability")
pdf.body_text(
    "Ducting for electric vehicle charging infrastructure has been laid as part of the ongoing "
    "Omeath modernisation works. However, the charging ports themselves have not yet been "
    "installed. The ducting is in place and ready for future connection."
)
pdf.section_divider()

pdf.heading2("2. Council Water Pumping Capabilities")
pdf.body_text(
    "Concerns were raised about the council's lack of water pumping capabilities. The flooding "
    "caused by sustained rainfall in January 2026 -- which brought significant flooding to parts "
    "of Louth including areas near Dundalk and the Cooley Peninsula -- highlighted the gap. The "
    "Fire Brigade was called out to one residential property that was at serious risk of flooding, "
    "prevented only by a boundary wall. Members stressed the need for the council to have its own "
    "pumping equipment to respond to flood events without sole reliance on emergency services."
)
pdf.section_divider()

pdf.heading2("3. Work Programme Update")
pdf.bullet("Louth Biodiversity Action Plan", " -- Commenced")
pdf.bullet("Tree Management Strategy", " -- Commenced")
pdf.bullet("Community Gardens and Allotments Strategy", " -- Commenced")
pdf.bullet("Pesticide Use Policy and Procedure for Louth County Council", " -- Commencing soon (presentation forthcoming)")
pdf.bullet("CLIMAAX Risk Assessment and Emerging Policies", " -- Commencing soon (presentation forthcoming)")
pdf.bullet("Mid-Programme Review", " -- Scheduled for Q4 2026; review of progress and consideration of additional policies")
pdf.bullet("Sustainable Flower Planter and Display Policy", " -- Delivery expected 2027")
pdf.bullet("Alien Invasive Species Plan for Louth", " -- Delivery expected 2027")
pdf.ln(2)
pdf.bold_body("Note on CLIMAAX: ", "This is an EU-funded framework (CLIMAte risk and vulnerability Assessment framework and toolboX) that supports regional and local authorities in carrying out climate risk assessments. Louth County Council's participation will inform emerging policies.")
pdf.section_divider()

pdf.heading2("4. National Tree Week")
pdf.body_text(
    "National Tree Week is scheduled for 8th-15th March 2026. Up to 1,200 native trees will be "
    "made available across the county to landowners free of charge, coordinated through the "
    "council's Biodiversity and Community Officer. The initiative supports both biodiversity "
    "goals and community engagement."
)
pdf.section_divider()

pdf.heading2("5. CMAP: Coastal Monitoring and Adaptation Planning")
pdf.body_text(
    "A presentation was delivered on the CMAP programme -- a four-year, cross-border initiative "
    "led by Ulster University and funded through PEACEPLUS (managed by SEUPB). Total investment "
    "is EUR 9.6 million (2025-2029), with 12 partner organisations including Newry, Mourne and "
    "Down District Council (lead partner) and RSPB."
)
pdf.body_text(
    "The programme will develop coastal monitoring policies across Northern Ireland and parts of "
    "the Republic of Ireland. Areas of focus relevant to Louth include Carlingford Lough, "
    "Dundalk Bay, and Baltray."
)

pdf.heading3("Key Work Packages Presented")

pdf.set_font("DejaVu", "B", 10)
pdf.set_text_color(*BLACK)
pdf.cell(0, 6, "Coastal Monitoring Protocols:")
pdf.ln(7)
pdf.sub_bullet("Implement monitoring protocols and datasets for sand, rock, and saltmarsh habitats")
pdf.sub_bullet("Engage with local communities")
pdf.sub_bullet("Monitor coastal erosion and develop solutions")
pdf.ln(2)

pdf.set_font("DejaVu", "B", 10)
pdf.set_text_color(*BLACK)
pdf.cell(0, 6, "WP2 -- Natural Capital, Habitats, Species and Human Behaviour:")
pdf.ln(7)
pdf.body_text(
    "Focused on habitat and species restoration, addressing biodiversity loss, climate change, "
    "and ecosystem degradation through scientific monitoring and community engagement."
)

pdf.bullet("Activity 2.1 -- Saltmarsh Biodiversity and Pressure Assessment:", " Dundalk is designated as a Saltmarsh Centre of Excellence, given it contains one of the largest saltmarshes in Ireland. Includes an education component. Uses the SMAATIE assessment tool (Saltmarsh Angiosperm Assessment Tool for Ireland), with 7 local assessments planned.")
pdf.bullet("Activity 2.2 -- Blue Carbon in Saltmarshes:", " Citizen science programme for fringe-marsh CO2 monitoring. Sampling 70 soil cores from 7 sites, plus gas flux sampling.")
pdf.bullet("Activity 2.3 -- Tern Conservation and Monitoring:", " Covers 5 tern species. Includes habitat restoration, predator control and surveillance, a ringing and releasing programme, development of an All-Island Tern Action Plan, and an offshore raft programme.")
pdf.bullet("Activity 2.4 -- Biosecurity Infrastructure Implementation:", " Establishment of a biosecurity team, with knowledge exchange drawing on experience from Rathlin Island.")
pdf.bullet("Activity 2.5 -- Seagrass and Shellfish Restoration:", " 75 moorings replaced in Strangford Lough to reduce habitat damage. Includes sediment sampling for carbon stock assessment, mini-buoy arrays for wave action monitoring, and citizen science participation.")
pdf.bullet("Activity 2.6 -- Building a Coastal Recovery Network:", " Development of a Coastal Recovery Partnership with MoU and governance structure. Collection of case studies and best practices. Includes a native oyster hatchery in Carlingford Lough.")
pdf.ln(2)
pdf.bold_body("Louth-specific outcomes: ", "Policies are expected to emerge from the programme over its four-year lifespan, with direct relevance to Carlingford Lough, Dundalk Bay, and Baltray. A Marine Project Officer post has been advertised by Louth County Council to support the programme locally.")
pdf.section_divider()

pdf.heading2("6. SuDS Training")
pdf.body_text(
    "Training on Sustainable Urban Drainage Systems (SuDS) is currently being rolled out across "
    "all local authorities."
)
pdf.section_divider()

pdf.heading2("7. EV Charging in Dunleer")
pdf.body_text(
    "Peter Dunne raised the issue of the public EV charger in Dunleer, which is either in need "
    "of repair or replacement. It was clarified that the existing charger is privately owned and "
    "there is currently no public charger in Dunleer. The Infrastructure SPC has been handling "
    "this matter. It was suggested that the committee could enquire about when an EV Officer for "
    "Louth will be appointed."
)
pdf.action_label("Committee Action Noted: Follow up with Infrastructure SPC / council on EV Officer appointment timeline and public charging provision for Dunleer.")
pdf.section_divider()

pdf.heading2("Committee Actions Noted")
pdf.bullet("Investigate council water pumping capabilities for flood response", " -- Council / Climate Action SPC")
pdf.bullet("Confirm timeline for EV charging port installation at Omeath", " -- Council")
pdf.bullet("Enquire about EV Officer appointment for Louth", " -- Infrastructure SPC")
pdf.bullet("Progress public EV charger provision for Dunleer", " -- Infrastructure SPC")
pdf.bullet("Pesticide Use Policy presentation to be scheduled", " -- Council officials")
pdf.bullet("CLIMAAX Risk Assessment presentation to be scheduled", " -- Council officials")

pdf.output("SPC_Summary_23_Feb_2026.pdf")
print("PDF generated: SPC_Summary_23_Feb_2026.pdf")
