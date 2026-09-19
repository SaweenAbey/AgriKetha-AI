import React, { useState, useEffect } from "react";
import {
  Crown,
  ShieldCheck,
  CheckCircle2,
  CreditCard,
  Smartphone,
  Wallet,
  X,
  Sparkles,
  Loader2,
  Lock,
  ArrowRight,
  Info,
  Check,
  AlertCircle,
  Copy,
  Receipt
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { paymentService } from "@/services/api";
import { useQuota } from "@/context/QuotaContext";
import { useLanguage } from "@/context/LanguageContext";

const TEST_CARDS = [
  {
    type: "Visa",
    number: "4111 1111 1111 1111",
    exp: "12/28",
    cvv: "123",
    otp: "1234",
    bank: "Commercial Bank (Sandbox)",
    bgGradient: "from-blue-600 to-indigo-700"
  },
  {
    type: "Mastercard",
    number: "5200 8282 8282 8282",
    exp: "09/29",
    cvv: "456",
    otp: "1234",
    bank: "HNB / Sampath (Sandbox)",
    bgGradient: "from-rose-600 to-amber-700"
  }
];

export const PaymentCheckoutModal = ({ isOpen, onClose, onPaymentSuccess }) => {
  const { fetchQuota } = useQuota();
  const { t, language } = useLanguage();

  const [selectedPlan, setSelectedPlan] = useState("pro_monthly"); // 'pro_monthly' | 'pro_annual'
  const [paymentMethod, setPaymentMethod] = useState("card"); // 'card' | 'genie' | 'ezcash'
  
  // Card form state
  const [cardNumber, setCardNumber] = useState("4111 1111 1111 1111");
  const [cardHolder, setCardHolder] = useState("FARMER SAMAN KUMARA");
  const [expiry, setExpiry] = useState("12/28");
  const [cvv, setCvv] = useState("123");
  const [phone, setPhone] = useState("077 123 4567");

  // Flow states: 'select' -> 'processing' -> '3ds_otp' -> 'success'
  const [step, setStep] = useState("select");
  const [otp, setOtp] = useState("1234");
  const [orderData, setOrderData] = useState(null);
  const [receipt, setReceipt] = useState(null);
  const [errorMsg, setErrorMsg] = useState("");
  const [copiedCard, setCopiedCard] = useState(null);

  // Reset when modal opens
  useEffect(() => {
    if (isOpen) {
      setStep("select");
      setErrorMsg("");
      setReceipt(null);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const currentPrice = selectedPlan === "pro_monthly" ? "1,500.00" : "14,400.00";
  const planTitle = selectedPlan === "pro_monthly" 
    ? (language === "si" ? "AgriKetha Pro (මාසික ගිණුම)" : "AgriKetha Pro (Monthly)") 
    : (language === "si" ? "AgriKetha Pro (වාර්ෂික ගිණුම - 20% ඉතිරියක්)" : "AgriKetha Pro (Annual - 20% OFF)");

  const handleFillTestCard = (card) => {
    setCardNumber(card.number);
    setExpiry(card.exp);
    setCvv(card.cvv);
    setCopiedCard(card.type);
    try {
      navigator.clipboard.writeText(card.number.replace(/\s+/g, ""));
    } catch (e) {
      // clipboard fallback
    }
    setTimeout(() => setCopiedCard(null), 2500);
  };

  const handleLaunchPayHereOfficialModal = async () => {
    setErrorMsg("");
    setStep("processing");

    try {
      const order = await paymentService.createOrder(selectedPlan, "payhere_official");
      setOrderData(order);

      if (window.payhere) {
        const payment = {
          sandbox: true,
          merchant_id: String(order.payhere.merchant_id).trim(),
          return_url: window.location.origin,
          cancel_url: window.location.origin,
          notify_url: "http://localhost:8000/api/v1/payments/payhere-notify",
          order_id: String(order.order_id).trim(),
          items: order.payhere.item_name || "AgriKetha Pro Plan",
          amount: parseFloat(order.amount).toFixed(2),
          currency: order.currency || "LKR",
          hash: String(order.payhere.hash).trim(),
          first_name: order.payhere.first_name || "Farmer",
          last_name: order.payhere.last_name || "User",
          email: order.payhere.email || "farmer@agriketha.ai",
          phone: order.payhere.phone || "0771234567",
          address: order.payhere.address || "Western Province",
          city: order.payhere.city || "Colombo",
          country: "Sri Lanka",
        };

        window.payhere.onCompleted = async function onCompleted(orderId) {
          try {
            const res = await paymentService.verifyPayment({
              order_id: orderId || order.order_id,
              status: "SUCCESS",
              payment_method: "payhere_official_popup",
            });
            setReceipt(res);
            setStep("success");
            await fetchQuota();
            if (onPaymentSuccess) onPaymentSuccess(res);
          } catch (vErr) {
            console.error("Verification error:", vErr);
            setStep("select");
          }
        };

        window.payhere.onDismissed = function onDismissed() {
          setStep("select");
        };

        window.payhere.onError = function onError(error) {
          console.error("PayHere Error:", error);
          setErrorMsg(typeof error === "string" ? error : "PayHere popup encountered an issue. Using instant simulator.");
          setStep("select");
        };

        window.payhere.startPayment(payment);
      } else {
        // Fallback to in-app simulated 3DS OTP
        setTimeout(() => setStep("3ds_otp"), 1000);
      }
    } catch (err) {
      console.error("PayHere launch error:", err);
      setErrorMsg(err.response?.data?.detail || "Could not launch PayHere SDK.");
      setStep("select");
    }
  };

  const handleInitiatePayment = async () => {
    setErrorMsg("");
    setStep("processing");

    try {
      // 1. Create Order via backend API
      const order = await paymentService.createOrder(selectedPlan, paymentMethod);
      setOrderData(order);

      // Simulate network verification & 3D Secure transition
      setTimeout(() => {
        setStep("3ds_otp");
      }, 1200);
    } catch (err) {
      console.error("Order creation error:", err);
      setErrorMsg(err.response?.data?.detail || "Could not initiate payment order.");
      setStep("select");
    }
  };

  const handleVerifyOtpAndComplete = async () => {
    if (otp.trim() !== "1234") {
      setErrorMsg(language === "si" ? "වැරදි OTP අංකයකි. කරුණාකර '1234' ඇතුළත් කරන්න." : "Invalid OTP. Please enter test OTP: 1234");
      return;
    }

    setStep("processing");
    setErrorMsg("");

    try {
      // 2. Call backend verification endpoint
      const res = await paymentService.verifyPayment({
        order_id: orderData?.order_id || `AGRI-TEST-${Date.now()}`,
        payment_id: `PAYHERE-SANDBOX-${Math.floor(100000 + Math.random() * 900000)}`,
        status: "SUCCESS",
        payment_method: paymentMethod,
        card_last4: cardNumber.replace(/\s+/g, "").slice(-4) || "1111"
      });

      setReceipt(res);
      setStep("success");

      // Refresh global quota so unlimited status takes effect immediately across all screens
      await fetchQuota();
      if (onPaymentSuccess) {
        onPaymentSuccess(res);
      }
    } catch (err) {
      console.error("Payment verification error:", err);
      setErrorMsg(err.response?.data?.detail || "Payment authorization failed.");
      setStep("3ds_otp");
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-md flex items-center justify-center p-3 sm:p-4 overflow-y-auto animate-in fade-in duration-200">
      <div className="bg-card border border-emerald-500/30 rounded-3xl max-w-xl w-full p-5 sm:p-7 shadow-2xl space-y-5 relative overflow-hidden my-auto">
        {/* Ambient glow */}
        <div className="absolute -top-24 -right-24 w-56 h-56 bg-amber-500/15 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -bottom-24 -left-24 w-56 h-56 bg-emerald-500/15 rounded-full blur-3xl pointer-events-none" />

        {/* Header with Close */}
        <div className="flex items-center justify-between border-b border-border/70 pb-3.5">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-gradient-to-tr from-amber-500 to-yellow-400 text-white shadow-md shadow-amber-500/20">
              <Crown className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-base sm:text-lg font-black text-foreground tracking-tight">
                  {language === "si" ? "AgriKetha Pro ආරක්ෂිත ගෙවීම" : "AgriKetha Pro Secure Checkout"}
                </h3>
                <Badge className="bg-amber-500/15 text-amber-600 dark:text-amber-400 border border-amber-500/30 text-[10px] uppercase font-bold">
                  🇱🇰 PayHere Sandbox
                </Badge>
              </div>
              <p className="text-[11px] text-muted-foreground">
                {language === "si" ? "256-bit SSL එන්ක්‍රිප්ට් කළ සත්‍ය පරීක්ෂණ ගෙවීම් දොරටුව" : "256-Bit SSL Encrypted Sri Lankan Payment Gateway"}
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="p-1.5 rounded-full bg-muted/60 hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Error Alert */}
        {errorMsg && (
          <div className="p-3 rounded-2xl bg-rose-500/10 border border-rose-500/30 text-rose-700 dark:text-rose-300 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0 text-rose-500" />
            <span className="flex-1">{errorMsg}</span>
          </div>
        )}

        {/* STEP 1: SELECT PLAN & ENTER PAYMENT */}
        {step === "select" && (
          <div className="space-y-4">
            {/* Plan Selector Buttons */}
            <div className="grid grid-cols-2 gap-2.5">
              <button
                type="button"
                onClick={() => setSelectedPlan("pro_monthly")}
                className={`p-3 rounded-2xl border text-left transition-all relative ${
                  selectedPlan === "pro_monthly"
                    ? "border-teal-500 bg-teal-500/10 shadow-sm"
                    : "border-border hover:bg-muted/40"
                }`}
              >
                <div className="text-xs font-bold text-foreground">Monthly Plan</div>
                <div className="text-sm sm:text-base font-black text-teal-600 dark:text-teal-400 mt-0.5">
                  LKR 1,500 <span className="text-[10px] text-muted-foreground font-normal">/ mo</span>
                </div>
                <div className="text-[10px] text-muted-foreground mt-1">Billed monthly, cancel anytime</div>
              </button>

              <button
                type="button"
                onClick={() => setSelectedPlan("pro_annual")}
                className={`p-3 rounded-2xl border text-left transition-all relative ${
                  selectedPlan === "pro_annual"
                    ? "border-amber-500 bg-amber-500/10 shadow-sm"
                    : "border-border hover:bg-muted/40"
                }`}
              >
                <Badge className="absolute -top-2 right-2 bg-gradient-to-r from-amber-500 to-yellow-500 text-white text-[9px] border-0">
                  SAVE 20%
                </Badge>
                <div className="text-xs font-bold text-foreground">Annual Plan</div>
                <div className="text-sm sm:text-base font-black text-amber-600 dark:text-amber-400 mt-0.5">
                  LKR 14,400 <span className="text-[10px] text-muted-foreground font-normal">/ yr</span>
                </div>
                <div className="text-[10px] text-muted-foreground mt-1">LKR 1,200/mo effective</div>
              </button>
            </div>

            {/* Payment Method Channels */}
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-foreground flex items-center justify-between">
                <span>Select Payment Method</span>
                <span className="text-[10px] text-muted-foreground">PayHere Multi-Channel</span>
              </label>
              <div className="grid grid-cols-3 gap-2">
                <button
                  type="button"
                  onClick={() => setPaymentMethod("card")}
                  className={`p-2.5 rounded-xl border flex flex-col items-center gap-1 text-xs font-semibold transition-all ${
                    paymentMethod === "card"
                      ? "border-teal-500 bg-teal-500/10 text-teal-600 dark:text-teal-400 shadow-sm"
                      : "border-border text-muted-foreground hover:bg-muted"
                  }`}
                >
                  <CreditCard className="w-4 h-4" />
                  <span>Cards (Visa/MC)</span>
                </button>

                <button
                  type="button"
                  onClick={() => setPaymentMethod("genie")}
                  className={`p-2.5 rounded-xl border flex flex-col items-center gap-1 text-xs font-semibold transition-all ${
                    paymentMethod === "genie"
                      ? "border-teal-500 bg-teal-500/10 text-teal-600 dark:text-teal-400 shadow-sm"
                      : "border-border text-muted-foreground hover:bg-muted"
                  }`}
                >
                  <Smartphone className="w-4 h-4" />
                  <span>Dialog Genie / FriMi</span>
                </button>

                <button
                  type="button"
                  onClick={() => setPaymentMethod("ezcash")}
                  className={`p-2.5 rounded-xl border flex flex-col items-center gap-1 text-xs font-semibold transition-all ${
                    paymentMethod === "ezcash"
                      ? "border-teal-500 bg-teal-500/10 text-teal-600 dark:text-teal-400 shadow-sm"
                      : "border-border text-muted-foreground hover:bg-muted"
                  }`}
                >
                  <Wallet className="w-4 h-4" />
                  <span>eZ Cash / mCash</span>
                </button>
              </div>
            </div>

            {/* Test Sandbox Presets Banner */}
            <div className="p-3 rounded-2xl bg-muted/40 border border-border/80 space-y-2">
              <div className="flex items-center justify-between text-xs font-semibold text-muted-foreground">
                <span className="flex items-center gap-1 text-foreground">
                  <Sparkles className="w-3.5 h-3.5 text-amber-500" />
                  Testing Sandbox Presets (1-Click Fill)
                </span>
                <span className="text-[10px] text-teal-600 dark:text-teal-400">Click to autofill</span>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
                {TEST_CARDS.map((c) => (
                  <button
                    key={c.type}
                    type="button"
                    onClick={() => handleFillTestCard(c)}
                    className="p-2 rounded-xl bg-background border border-border/70 hover:border-teal-500 text-left transition-all flex items-center justify-between text-xs"
                  >
                    <div>
                      <span className="font-bold text-foreground">{c.type}</span>
                      <span className="text-muted-foreground text-[11px] block">{c.number}</span>
                    </div>
                    {copiedCard === c.type ? (
                      <Check className="w-3.5 h-3.5 text-emerald-500" />
                    ) : (
                      <Copy className="w-3 h-3 text-muted-foreground" />
                    )}
                  </button>
                ))}
              </div>
            </div>

            {/* Card Form */}
            {paymentMethod === "card" ? (
              <div className="space-y-2.5 p-3.5 rounded-2xl bg-muted/20 border border-border">
                <div>
                  <label className="text-[11px] font-semibold text-muted-foreground block mb-1">Card Number</label>
                  <div className="relative">
                    <input
                      type="text"
                      value={cardNumber}
                      onChange={(e) => setCardNumber(e.target.value)}
                      placeholder="4111 1111 1111 1111"
                      className="w-full h-9 px-3 rounded-xl bg-background border border-border text-xs font-mono font-medium focus:ring-1 focus:ring-teal-500 focus:outline-none"
                    />
                    <CreditCard className="w-4 h-4 text-muted-foreground absolute right-3 top-2.5" />
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-2">
                  <div className="col-span-2">
                    <label className="text-[11px] font-semibold text-muted-foreground block mb-1">Cardholder Name</label>
                    <input
                      type="text"
                      value={cardHolder}
                      onChange={(e) => setCardHolder(e.target.value)}
                      className="w-full h-9 px-3 rounded-xl bg-background border border-border text-xs font-medium focus:ring-1 focus:ring-teal-500 focus:outline-none uppercase"
                    />
                  </div>
                  <div>
                    <label className="text-[11px] font-semibold text-muted-foreground block mb-1">Expiry / CVV</label>
                    <div className="flex gap-1">
                      <input
                        type="text"
                        value={expiry}
                        onChange={(e) => setExpiry(e.target.value)}
                        placeholder="MM/YY"
                        className="w-1/2 h-9 px-2 rounded-xl bg-background border border-border text-xs font-mono text-center focus:ring-1 focus:ring-teal-500 focus:outline-none"
                      />
                      <input
                        type="text"
                        value={cvv}
                        onChange={(e) => setCvv(e.target.value)}
                        placeholder="CVV"
                        className="w-1/2 h-9 px-2 rounded-xl bg-background border border-border text-xs font-mono text-center focus:ring-1 focus:ring-teal-500 focus:outline-none"
                      />
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="space-y-2 p-3.5 rounded-2xl bg-muted/20 border border-border">
                <label className="text-[11px] font-semibold text-muted-foreground block">
                  {paymentMethod === "genie" ? "Dialog Genie Registered Mobile" : "eZ Cash Mobile Number"}
                </label>
                <input
                  type="text"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  className="w-full h-9 px-3 rounded-xl bg-background border border-border text-xs font-mono focus:ring-1 focus:ring-teal-500 focus:outline-none"
                />
              </div>
            )}

            {/* Action Buttons: Official PayHere Popup & In-App Simulator */}
            <div className="space-y-2 pt-1">
              <Button
                type="button"
                onClick={handleLaunchPayHereOfficialModal}
                className="w-full h-11 rounded-2xl bg-gradient-to-r from-amber-500 to-yellow-500 hover:from-amber-600 hover:to-yellow-600 text-slate-950 font-black text-xs shadow-lg shadow-amber-500/20 gap-2"
              >
                <Crown className="w-4 h-4" />
                <span>Launch PayHere Official Popup (LKR {currentPrice})</span>
              </Button>

              <Button
                type="button"
                onClick={handleInitiatePayment}
                variant="outline"
                className="w-full h-10 rounded-2xl border-border hover:bg-muted font-bold text-xs gap-2"
              >
                <Lock className="w-3.5 h-3.5 text-teal-600" />
                <span>Instant In-App Sandbox Checkout</span>
              </Button>
            </div>
          </div>
        )}

        {/* STEP 2: PROCESSING ANIMATION */}
        {step === "processing" && (
          <div className="py-12 text-center space-y-4">
            <div className="w-16 h-16 rounded-full bg-teal-500/10 text-teal-600 dark:text-teal-400 flex items-center justify-center mx-auto animate-pulse">
              <Loader2 className="w-8 h-8 animate-spin" />
            </div>
            <div>
              <h4 className="text-base font-bold text-foreground">Processing PayHere Sandbox Transaction...</h4>
              <p className="text-xs text-muted-foreground mt-1">Connecting to Sri Lanka Interbank Payment Network (LankaPay)...</p>
            </div>
          </div>
        )}

        {/* STEP 3: 3D SECURE OTP SIMULATOR */}
        {step === "3ds_otp" && (
          <div className="space-y-4 animate-in fade-in">
            <div className="p-4 rounded-2xl bg-blue-500/10 border border-blue-500/30 space-y-2">
              <div className="flex items-center gap-2 text-xs font-bold text-blue-600 dark:text-blue-400">
                <ShieldCheck className="w-4 h-4" />
                <span>3D Secure 2.0 • LankaPay Verification</span>
              </div>
              <p className="text-[11px] text-muted-foreground">
                A test One-Time Password (OTP) has been dispatched to your mobile number. For sandbox testing, enter <b>1234</b>.
              </p>
            </div>

            <div className="space-y-1.5 text-center py-2">
              <label className="text-xs font-semibold text-muted-foreground block">Enter 4-Digit Security OTP</label>
              <input
                type="text"
                maxLength={4}
                value={otp}
                onChange={(e) => setOtp(e.target.value)}
                className="w-36 h-11 text-center font-mono text-xl tracking-widest font-black rounded-xl bg-background border border-teal-500 mx-auto block focus:ring-2 focus:ring-teal-500 focus:outline-none"
              />
              <span className="text-[10px] text-muted-foreground">Sandbox default: <b>1234</b></span>
            </div>

            <Button
              type="button"
              onClick={handleVerifyOtpAndComplete}
              className="w-full h-11 rounded-2xl bg-gradient-to-r from-emerald-600 to-teal-600 text-white font-bold text-xs shadow-lg shadow-emerald-600/20 gap-2"
            >
              <CheckCircle2 className="w-4 h-4" />
              <span>Verify OTP & Complete Authorization</span>
            </Button>
          </div>
        )}

        {/* STEP 4: PAYMENT SUCCESS RECEIPT */}
        {step === "success" && (
          <div className="space-y-4 text-center py-2 animate-in zoom-in-95 duration-200">
            <div className="w-14 h-14 rounded-full bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 flex items-center justify-center mx-auto shadow-lg shadow-emerald-500/20">
              <CheckCircle2 className="w-8 h-8" />
            </div>

            <div>
              <h4 className="text-lg font-black text-foreground">
                {language === "si" ? "ගෙවීම සාර්ථකයි! Pro සක්‍රිය විය." : "Payment Verified Successfully!"}
              </h4>
              <p className="text-xs text-muted-foreground mt-0.5">
                {language === "si" 
                  ? "ඔබගේ AgriKetha Pro අසීමිත ගිණුම දැන් සක්‍රිය කර ඇත."
                  : "Your AgriKetha Pro Unlimited plan is now active with zero daily limits."}
              </p>
            </div>

            {/* Receipt Card */}
            <div className="p-4 rounded-2xl bg-muted/40 border border-border/80 text-left text-xs space-y-2">
              <div className="flex items-center justify-between border-b border-border/50 pb-2">
                <span className="text-muted-foreground flex items-center gap-1">
                  <Receipt className="w-3.5 h-3.5 text-teal-600" />
                  Order Ref:
                </span>
                <span className="font-mono font-bold text-foreground">{receipt?.order_id || "AGRI-PRO-SANDBOX"}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Amount Paid:</span>
                <span className="font-bold text-emerald-600 dark:text-emerald-400">LKR {currentPrice}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Subscription Status:</span>
                <Badge className="bg-emerald-500/20 text-emerald-600 dark:text-emerald-400 border-0 font-bold text-[10px]">
                  👑 ACTIVE (UNLIMITED)
                </Badge>
              </div>
            </div>

            <Button
              type="button"
              onClick={onClose}
              className="w-full h-10 rounded-xl bg-teal-600 hover:bg-teal-700 text-white font-bold text-xs shadow-md"
            >
              Continue to AI Farming Dashboard
            </Button>
          </div>
        )}
      </div>
    </div>
  );
};
