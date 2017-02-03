import requests
import re
import math
import json


class Blueprint:

    def __init__(self, products, materials):
        self.products = products
        self.materials = materials


def stringparser():
    file = ""
    sentinel = ""

    file += "\n".join(iter(input, sentinel))
    # handling multiline inputs

    printdict = {}  # key: bpc name, value: number of runs
    counter = 0  # counts words
    badcount = 0  # counts lines that are not bpc

    rivi = file.rstrip()
    p = rivi.split("\n")
    # making the multiline input a list

    for i in range(0, len(p)):
        p[i] = re.sub("\t", " ", p[i])
        rivi = p[i].split(" ")
        # an individual line is now a list of words

        check = True

        if "BLUEPRINT" in rivi and "COPY" in rivi:
            # ensures the line is about a bpc

            for word in rivi:
                counter += 1
                # starts reading the words one by one

                if word == "Blueprint" and check is True:
                    printti = " ".join(rivi[:counter])
                    # combines the words to a string

                    if printti[0] == " ":
                        printti = printti[1:]
                        # removes the extra whitespace in some contracts
                    check = False
                    # only the first instance of "Blueprint" counts

                if word == "Runs:":
                    runienmäärä = int(rivi[counter])
                    # figures out the number of runs in the bpc

                    if printti in printdict.keys():
                        printdict[printti] += runienmäärä
                        # if the bpc is in the dict, add the number of runs
                    else:
                        printdict[printti] = runienmäärä
                        # else add the bpc to dict AND the number of runs

                    counter = 0
                    # step over to the next line in input
                    break

        else:
            badcount += 1
            # adds 1 if the line was not about a bpc

    print("Found", badcount, "invalid lines.")
    return printdict  # returns names and runs for the blueprints in userinput


def billofmaterials(namedict, bpdict, search):
    bom = []
    product = []
    if search in namedict.keys():
        name = str(namedict[search])
        # ID for the thing we can name: name is stored in "search" variable
        both = bpdict[name]
        matlincs = both.materials
        # retrieving the list of dicts that have one key and one value: quantity and material ID
        prodlincs = both.products
        # retrieving the list of product ID's
        for i in range(len(matlincs)):
            matdict = matlincs[i]
            # look for the material item ID for the i:th member in the material list
            idx = str(matdict["typeID"])
            # ID for material
            bom.append(idx)

        lincs = str(prodlincs["typeID"])
        # ID for endproduct
        product.append(lincs)
    else:
        print("404")

    return bom, product


def pc(namedict, bpdict, search, dictator, hms):
    totalmats = 0
    if search in namedict.keys():
        name = str(namedict[search])
        both = bpdict[name]
        matlincs = both.materials
        prodlincs = both.products
        for i in range(len(matlincs)):
            matdict = matlincs[i]
            idx = str(matdict["typeID"])
            price = dictator[idx]
            price *= int(matdict["quantity"])
            totalmats += price

        proddict = prodlincs
        idx = str(proddict["typeID"])
        buyprice = hms[idx][0]
        buyprice *= int(proddict["quantity"])
        sellprice = hms[idx][1]
        sellprice *= int(proddict["quantity"])

        instaprofit = buyprice - totalmats
        potentialprofit = sellprice - totalmats

        if instaprofit < 0:
            instaprofit = 0
        if potentialprofit < 0:
            potentialprofit = 0
        return instaprofit, potentialprofit

    else:
        print("404")


def main():
    print("Loading...")

    bpdict = {}  # key: print ID, value: bpc object

    with open('blueprints.json', 'r') as fp:
        bpdict1 = json.load(fp)  # key: name of item, value: item ID

    for avain in bpdict1:
        bpdict[str(avain)] = Blueprint(bpdict1[str(avain)][0], bpdict1[str(avain)][1])
    print("Done loading blueprint information. Loading the ID database...")

    with open('typeIDs.json', 'r') as fp:
        namedict = json.load(fp)  # key: name of item, value: item ID

    print("Done loading the database. System ready.")
    # program is now ready to accept inputs

    # the actual pc part starts here
    while True:
        tinstval = 0
        ttotalval = 0
        bom = []  # item ID's for all required materials in this contract
        products = []  # item ID's for all products in this contract
        printdict = stringparser()  # names and runs for all blueprints in userinput
        dictator = {}  # key: item ID, value: ISK price for that item (materials)
        hms = {}  # key: item ID for product, value: [maximum buy, minimum sell]
        thefinaldict = {}  # key: bpc name, value: total ISK value for bpc

        if printdict:

            print("Processing...")
            for searchkey in printdict.keys():
                # searchkey: blueprint name
                z = billofmaterials(namedict, bpdict, searchkey)
                x = z[0]
                y = z[1]
                # returns a list that contains the materials needed
                bom.extend(x)
                products.extend(y)

            bom = list(set(bom))
            products = list(set(products))
            bom = list(bom)
            products = list(products)

            for i in range(math.ceil(len(bom)/50)):
                link = "http://api.eve-central.com/api/marketstat/json?"
                for h in range(50):
                    try:
                        boom = bom[h]
                        link = link + "typeid=" + boom + "&"
                    except IndexError:
                        break

                link += "usesystem=30000142"
                r = requests.get(link)
                prices = r.json()
                for h in range(len(prices)):
                    e = prices[h]
                    sell = e["sell"]
                    minsell = sell["min"]
                    dictator[bom[h]] = minsell

                del bom[:50]

            for i in range(math.ceil(len(products)/50)):
                link = "http://api.eve-central.com/api/marketstat/json?"
                for h in range(50):
                    try:
                        produkter = products[h]
                        link = link + "typeid=" + produkter + "&"
                    except IndexError:
                        break

                link += "usesystem=30000142"
                r = requests.get(link)
                productprices = r.json()

                for h in range(len(productprices)):
                    e = productprices[h]
                    sell = e["sell"]
                    minsell = sell["min"]
                    buy = e["buy"]
                    maxbuy = buy["max"]
                    hms[products[h]] = maxbuy, minsell
                del products[:50]

            for searchkey in sorted(printdict.keys()):
                px = pc(namedict, bpdict, searchkey, dictator, hms)
                printbuyvalue = px[0]
                printsellvalue = px[1]
                totalruns = printdict[searchkey]
                totalprintbuyvalue = printbuyvalue * totalruns
                tinstval += totalprintbuyvalue
                totalprintsellvalue = printsellvalue * totalruns
                ttotalval += totalprintsellvalue
                thefinaldict[searchkey] = totalprintbuyvalue, totalprintsellvalue

            d_view = [(v, k) for k, v in thefinaldict.items()]
            d_view.sort()
            for v, k in d_view:
                instval = v[0] / 1000000
                totalval = v[1] / 1000000

                print(k, " Total runs: ", printdict[k], " Instant value: {:.3f}m ISK, Total value {:.3f}m ISK".format(instval, totalval))

            print("Total value of contract: {:.3f}m ISK or {:.3f}m ISK".format(tinstval / 1000000, ttotalval / 1000000))

        else:
            pass

main()
